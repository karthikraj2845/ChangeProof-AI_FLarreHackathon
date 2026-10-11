import pytest
from app.db.session import SessionLocal
from app.orchestration.runner import WorkflowRunner


def test_langgraph_workflow_execution_and_resumption():
    db = SessionLocal()
    try:
        # Start workflow
        state = WorkflowRunner.start_change_assurance(
            db=db,
            change_request_id="CR-2026-001",
            user_request="Remove the jurisdiction restriction from the safe-driver discount eligibility rule.",
        )

        assert "workflow_id" in state
        wf_id = state["workflow_id"]
        assert state["status"] in ["PAUSED_FOR_REVIEW", "BLOCKED", "COMPLETED"]
        assert state["target_rule_id"] == "RULE-SAFE-DRIVER"
        assert len(state.get("test_results", [])) == 8
        assert state.get("readiness_result", {}).get("status") == "BLOCKED"

        # Resume workflow with human decision
        resumed_state = WorkflowRunner.resume_with_review(
            db=db,
            workflow_id=wf_id,
            reviewer="Senior Underwriting Officer",
            action="REJECT",
            justification="Blocked due to verified jurisdiction defect in NV.",
        )
        assert resumed_state["status"] == "REJECTED"
        assert resumed_state["human_review_decision"]["reviewer"] == "Senior Underwriting Officer"
    finally:
        db.close()
