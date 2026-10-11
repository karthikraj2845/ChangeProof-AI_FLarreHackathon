from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.change import ChangeRequest
from app.models.workflow import WorkflowRun
from app.models.audit import AuditEvent
from app.orchestration.graph_builder import change_assurance_app
from app.orchestration.state import WorkflowState


def serialize_for_json(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [serialize_for_json(v) for v in obj]
    return obj



class WorkflowRunner:
    """
    Manages workflow execution lifecycle, persistence, state transitions, and audit records.
    """

    @classmethod
    def start_change_assurance(
        cls,
        db: Session,
        change_request_id: str,
        user_request: Optional[str] = None,
    ) -> Dict[str, Any]:
        cr = db.query(ChangeRequest).filter_by(id=change_request_id).first()
        if not cr:
            raise ValueError(f"Change request {change_request_id} not found.")

        req_text = user_request or cr.description
        workflow_id = f"WF-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc)

        # 1. Initialize DB workflow run record
        wf_record = WorkflowRun(
            id=workflow_id,
            change_request_id=change_request_id,
            workflow_type="CHANGE_ASSURANCE",
            status="RUNNING",
            current_node="start",
            state_json={},
            start_time=now,
        )
        db.add(wf_record)

        audit = AuditEvent(
            id=f"AUDIT-WF-START-{workflow_id}",
            event_type="WORKFLOW_STARTED",
            entity_type="WORKFLOW_RUN",
            entity_id=workflow_id,
            actor="SYSTEM",
            details={"change_request_id": change_request_id, "user_request": req_text},
            timestamp=now,
        )
        db.add(audit)
        db.commit()

        # 2. Prepare initial LangGraph state
        initial_state: WorkflowState = {
            "workflow_id": workflow_id,
            "change_request_id": change_request_id,
            "user_request": req_text,
            "target_rule_id": cr.target_rule_id,
            "baseline_version_id": cr.baseline_version_id,
            "proposed_version_id": cr.proposed_version_id,
            "current_stage": "start",
            "status": "RUNNING",
            "errors": [],
            "warnings": [],
            "execution_metadata": {},
        }

        # 3. Invoke LangGraph with thread configuration for checkpointing
        config = {"configurable": {"thread_id": workflow_id}}
        final_state = change_assurance_app.invoke(initial_state, config=config)

        # 4. Update workflow run record in DB
        wf_record.status = final_state.get("status", "COMPLETED")
        wf_record.current_node = final_state.get("current_stage", "completed")
        wf_record.state_json = serialize_for_json(dict(final_state))
        if wf_record.status in ["COMPLETED", "BLOCKED"]:
            wf_record.completion_time = datetime.now(timezone.utc)

        db.commit()

        return dict(final_state)


    @classmethod
    def resume_with_review(
        cls,
        db: Session,
        workflow_id: str,
        reviewer: str,
        action: str,  # APPROVE, REJECT, REQUEST_MORE_TESTS
        justification: str,
    ) -> Dict[str, Any]:
        wf_record = db.query(WorkflowRun).filter_by(id=workflow_id).first()
        if not wf_record:
            raise ValueError(f"Workflow run {workflow_id} not found.")

        now = datetime.now(timezone.utc)
        decision = {
            "reviewer": reviewer,
            "action": action,
            "justification": justification,
            "timestamp": now.isoformat(),
        }

        # Fetch state from record
        state = dict(wf_record.state_json or {})
        state["human_review_decision"] = decision
        state["status"] = "APPROVED" if action == "APPROVE" else "REJECTED"
        state["current_stage"] = "human_review_gate"

        wf_record.status = state["status"]
        wf_record.state_json = serialize_for_json(state)
        wf_record.completion_time = now


        # Update change request status
        cr = db.query(ChangeRequest).filter_by(id=wf_record.change_request_id).first()
        if cr:
            cr.status = "APPROVED" if action == "APPROVE" else "REJECTED"

        audit = AuditEvent(
            id=f"AUDIT-REV-{uuid.uuid4().hex[:6]}",
            event_type=f"HUMAN_REVIEW_{action}",
            entity_type="WORKFLOW_RUN",
            entity_id=workflow_id,
            actor=reviewer,
            details=decision,
            timestamp=now,
        )
        db.add(audit)
        db.commit()

        return state
