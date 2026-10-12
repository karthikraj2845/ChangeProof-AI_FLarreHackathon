import pytest
from app.db.session import SessionLocal
from app.orchestration.runner import WorkflowRunner
from app.services.snapshot_service import SnapshotService


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
        assert state["status"] in ["PAUSED_FOR_REVIEW", "BLOCKED", "NEEDS_HUMAN_REVIEW"]
        assert state["target_rule_id"] == "RULE-SAFE-DRIVER"
        assert len(state.get("test_results", [])) == 8
        assert state.get("readiness_result", {}).get("status") == "BLOCKED"
        assert state.get("snapshot_id") is not None
        assert state.get("snapshot_hash") is not None

        # Verify Evidence Snapshot is cryptographically valid
        validity = SnapshotService.verify_snapshot_validity(db, state["snapshot_id"])
        assert validity["valid"] is True
        assert validity["stale"] is False

        # Attempt to override blocker with APPROVE: Must be rejected by governance
        with pytest.raises(ValueError, match="GOVERNANCE VIOLATION"):
            WorkflowRunner.resume_with_review(
                db=db,
                workflow_id=wf_id,
                reviewer="Overriding Manager",
                action="APPROVE",
                justification="Attempting to force approval despite regression.",
            )

        # Resume workflow with valid rejection
        resumed_state = WorkflowRunner.resume_with_review(
            db=db,
            workflow_id=wf_id,
            reviewer="Senior Underwriting Officer",
            action="REJECT",
            justification="Blocked due to verified jurisdiction defect in NV.",
        )
        assert resumed_state["status"] == "REJECTED"
        assert resumed_state["human_review_decision"]["reviewer"] == "Senior Underwriting Officer"

        # Attempt duplicate submission: Must fail
        with pytest.raises(ValueError, match="Cannot submit duplicate review"):
            WorkflowRunner.resume_with_review(
                db=db,
                workflow_id=wf_id,
                reviewer="Senior Underwriting Officer",
                action="REJECT",
                justification="Duplicate rejection submission.",
            )
    finally:
        db.close()


def test_langgraph_revision_request_routing():
    db = SessionLocal()
    try:
        state = WorkflowRunner.start_change_assurance(
            db=db,
            change_request_id="CR-2026-001",
            user_request="Remove the jurisdiction restriction from the safe-driver discount eligibility rule.",
        )
        wf_id = state["workflow_id"]

        # Request revision / more tests
        resumed = WorkflowRunner.resume_with_review(
            db=db,
            workflow_id=wf_id,
            reviewer="Lead Pricing Actuary",
            action="REQUEST_MORE_TESTS",
            justification="Need additional multi-vehicle tests before release decision.",
        )
        assert resumed["status"] == "REVISION_REQUIRED"
        assert resumed["human_review_decision"]["action"] == "REVISION_REQUIRED"
    finally:
        db.close()
