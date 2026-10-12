from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.change import ChangeRequest
from app.models.workflow import WorkflowRun
from app.models.audit import AuditEvent
from app.services.snapshot_service import SnapshotService
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
    Coordinates genuine LangGraph resumption, durable checkpointing, and cryptographic governance.
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
            id=f"AUDIT-WF-START-{workflow_id}-{uuid.uuid4().hex[:4].upper()}",
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
        wf_record.status = final_state.get("status", "PAUSED_FOR_REVIEW")
        wf_record.current_node = final_state.get("current_stage", "readiness_assessment")
        wf_record.state_json = serialize_for_json(dict(final_state))
        db.commit()

        # Record audit event for pause
        pause_audit = AuditEvent(
            id=f"AUDIT-WF-PAUSE-{workflow_id}-{uuid.uuid4().hex[:4].upper()}",
            event_type="WORKFLOW_PAUSED_AT_GATE",
            entity_type="WORKFLOW_RUN",
            entity_id=workflow_id,
            actor="SYSTEM",
            details={
                "status": wf_record.status,
                "snapshot_id": final_state.get("snapshot_id"),
                "readiness": final_state.get("readiness_result", {}).get("status"),
            },
            timestamp=datetime.now(timezone.utc),
        )
        db.add(pause_audit)
        db.commit()

        return dict(final_state)

    @classmethod
    def resume_with_review(
        cls,
        db: Session,
        workflow_id: str,
        reviewer: str,
        action: str,  # APPROVE, REJECT, REQUEST_MORE_TESTS, REVISION_REQUIRED
        justification: str,
        snapshot_id: Optional[str] = None,
        snapshot_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Resumes the paused LangGraph workflow from its checkpoint after validating
        evidence snapshot integrity and enforcing strict release readiness governance.
        """
        wf_record = db.query(WorkflowRun).filter_by(id=workflow_id).first()
        if not wf_record:
            raise ValueError(f"Workflow run {workflow_id} not found.")

        # Prevent duplicate submissions
        if wf_record.status in ["APPROVED", "REJECTED", "REVISION_REQUIRED"] and wf_record.completion_time is not None:
            raise ValueError(f"Workflow {workflow_id} has already concluded with status '{wf_record.status}'. Cannot submit duplicate review.")

        normalized_action = action.upper()
        if normalized_action == "REQUEST_MORE_TESTS":
            normalized_action = "REVISION_REQUIRED"

        valid_actions = {"APPROVE", "REJECT", "REVISION_REQUIRED"}
        if normalized_action not in valid_actions:
            raise ValueError(f"Invalid review action '{action}'. Permitted actions: {sorted(list(valid_actions))}")

        state = dict(wf_record.state_json or {})
        readiness = state.get("readiness_result", {})
        is_blocked = readiness.get("is_blocked", False) or readiness.get("status") == "BLOCKED"

        # Governance Rule 1: Ordinary human approval CANNOT override a failed regression suite
        if normalized_action == "APPROVE" and is_blocked:
            denial_audit = AuditEvent(
                id=f"AUDIT-DENIED-{uuid.uuid4().hex[:6]}-{uuid.uuid4().hex[:4].upper()}",
                event_type="APPROVAL_ATTEMPT_DENIED_REGRESSION_BLOCK",
                entity_type="WORKFLOW_RUN",
                entity_id=workflow_id,
                actor=reviewer,
                details={"action": normalized_action, "justification": justification, "reason": "Deterministic policy blocker active"},
                timestamp=datetime.now(timezone.utc),
            )
            db.add(denial_audit)
            db.commit()
            raise ValueError(
                "GOVERNANCE VIOLATION: Cannot approve change. Release is strictly BLOCKED by deterministic "
                "readiness policy due to behavioral regressions or test failures."
            )

        # Governance Rule 2: Verify Evidence Snapshot Integrity, Freshness, and Run Isolation
        effective_snapshot_id = snapshot_id or state.get("snapshot_id")
        effective_snapshot_hash = snapshot_hash or state.get("snapshot_hash")

        if normalized_action == "APPROVE":
            if not effective_snapshot_id:
                denial_audit = AuditEvent(
                    id=f"AUDIT-DENIED-{uuid.uuid4().hex[:6]}-{uuid.uuid4().hex[:4].upper()}",
                    event_type="APPROVAL_ATTEMPT_DENIED_NO_SNAPSHOT",
                    entity_type="WORKFLOW_RUN",
                    entity_id=workflow_id,
                    actor=reviewer,
                    details={"action": normalized_action, "justification": justification, "reason": "No evidence snapshot bound"},
                    timestamp=datetime.now(timezone.utc),
                )
                db.add(denial_audit)
                db.commit()
                raise ValueError("GOVERNANCE VIOLATION: Cannot approve change without a valid, persisted Evidence Snapshot.")

            # Validate reviewed hash if provided explicitly
            if snapshot_hash and state.get("snapshot_hash") and snapshot_hash != state.get("snapshot_hash"):
                denial_audit = AuditEvent(
                    id=f"AUDIT-DENIED-{uuid.uuid4().hex[:6]}-{uuid.uuid4().hex[:4].upper()}",
                    event_type="APPROVAL_ATTEMPT_DENIED_HASH_MISMATCH",
                    entity_type="WORKFLOW_RUN",
                    entity_id=workflow_id,
                    actor=reviewer,
                    details={"action": normalized_action, "justification": justification, "reason": "Reviewed snapshot hash does not match run checkpoint snapshot hash"},
                    timestamp=datetime.now(timezone.utc),
                )
                db.add(denial_audit)
                db.commit()
                raise ValueError(f"EVIDENCE HASH MISMATCH: Human reviewed hash '{snapshot_hash}' does not match workflow run hash '{state.get('snapshot_hash')}'.")

        if effective_snapshot_id:
            validity = SnapshotService.verify_snapshot_validity(
                db=db,
                snapshot_id=effective_snapshot_id,
                expected_workflow_run_id=workflow_id,
                expected_change_request_id=wf_record.change_request_id,
                expected_snapshot_hash=effective_snapshot_hash,
            )
            if not validity["valid"]:
                denial_audit = AuditEvent(
                    id=f"AUDIT-DENIED-{uuid.uuid4().hex[:6]}-{uuid.uuid4().hex[:4].upper()}",
                    event_type="APPROVAL_ATTEMPT_DENIED_INVALID_EVIDENCE",
                    entity_type="WORKFLOW_RUN",
                    entity_id=workflow_id,
                    actor=reviewer,
                    details={"action": normalized_action, "justification": justification, "reason": validity.get("reason"), "snapshot_id": effective_snapshot_id},
                    timestamp=datetime.now(timezone.utc),
                )
                db.add(denial_audit)
                db.commit()
                raise ValueError(f"STALE OR INVALID EVIDENCE: {validity.get('reason')}")

        now = datetime.now(timezone.utc)
        decision = {
            "reviewer": reviewer,
            "action": normalized_action,
            "justification": justification,
            "snapshot_id": effective_snapshot_id,
            "snapshot_hash": effective_snapshot_hash,
            "timestamp": now.isoformat(),
        }

        # 1. Update LangGraph checkpoint state via update_state
        config = {"configurable": {"thread_id": workflow_id}}
        change_assurance_app.update_state(
            config,
            {"human_review_decision": decision},
            as_node="readiness_assessment",
        )

        # 2. Resume execution across the human_review_gate node to END
        resumed_state = change_assurance_app.invoke(None, config=config)

        # 3. Determine final status
        final_status = resumed_state.get("status", "COMPLETED")
        if normalized_action == "APPROVE" and not is_blocked:
            db_status = "APPROVED"
        elif normalized_action == "REJECT":
            db_status = "REJECTED"
        elif normalized_action in ["REVISION_REQUIRED", "REQUEST_MORE_TESTS"]:
            db_status = "REVISION_REQUIRED"
        else:
            db_status = "BLOCKED"

        resumed_state["status"] = db_status

        # 4. Update DB workflow record
        wf_record.status = db_status
        wf_record.current_node = resumed_state.get("current_stage", "human_review_gate")
        wf_record.state_json = serialize_for_json(dict(resumed_state))
        wf_record.completion_time = now

        # 5. Update ChangeRequest record
        cr = db.query(ChangeRequest).filter_by(id=wf_record.change_request_id).first()
        if cr:
            cr.status = db_status

        # 6. Record Audit Event
        audit = AuditEvent(
            id=f"AUDIT-REV-{uuid.uuid4().hex[:6]}-{uuid.uuid4().hex[:4].upper()}",
            event_type=f"HUMAN_REVIEW_{normalized_action}",
            entity_type="WORKFLOW_RUN",
            entity_id=workflow_id,
            actor=reviewer,
            details={**decision, "resulting_status": db_status},
            timestamp=now,
        )
        db.add(audit)
        db.commit()

        return dict(resumed_state)
