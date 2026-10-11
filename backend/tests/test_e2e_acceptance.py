import pytest
from app.db.session import SessionLocal
from app.db.seed import seed_database
from app.models.change import ChangeRequest
from app.models.finding import Finding
from app.models.audit import AuditEvent
from app.orchestration.runner import WorkflowRunner
from app.verification.intent_guard import IntentGuardVerifier


def test_mandatory_end_to_end_acceptance():
    """
    Mandatory End-to-End Acceptance Test (Section 16 of specifications)
    Executes the complete vertical slice from clean seeded state through
    change analysis, regression detection, human review, IntentGuard simulation,
    finding generation, and audit verification.
    """
    db = SessionLocal()
    try:
        # Step 1: Clean seed of fictional motor insurance scenario
        seed_database(db)

        # Step 2: Open the rule change request (CR-2026-001)
        cr = db.query(ChangeRequest).filter_by(id="CR-2026-001").first()
        assert cr is not None
        assert "jurisdiction" in cr.title.lower()

        # Step 3 & 4: Start change-assurance workflow and observe LangGraph nodes
        workflow_state = WorkflowRunner.start_change_assurance(
            db=db,
            change_request_id=cr.id,
            user_request=cr.description,
        )
        assert workflow_state["workflow_id"] is not None
        assert workflow_state["current_stage"] in ["readiness_assessment", "human_review_gate"]

        # Step 5: View impacted artifacts & dependency paths
        impacted = workflow_state.get("impacted_artifacts", [])
        assert len(impacted) > 0
        paths = workflow_state.get("dependency_paths", [])
        assert len(paths) > 0

        # Step 6 & 7: Execute tests and detect the incorrect discount in NV (TEST-SD-002)
        test_results = workflow_state.get("test_results", [])
        assert len(test_results) == 8

        seeded_regression = next(t for t in test_results if t["test_id"] == "TEST-SD-002")
        assert seeded_regression["status"] == "REGRESSION"
        assert seeded_regression["baseline_outcome"]["eligible"] is False
        assert seeded_regression["proposed_outcome"]["eligible"] is True

        # Step 8: Check coverage summary
        coverage_gaps = workflow_state.get("coverage_gaps", [])
        assert isinstance(coverage_gaps, list)

        # Step 9: Generate readiness report - Must be BLOCKED
        readiness = workflow_state.get("readiness_result", {})
        assert readiness["status"] == "BLOCKED"
        assert readiness["is_blocked"] is True
        assert len(readiness["blockers"]) > 0

        # Step 10: Submit a human review decision (Rejecting the defective release)
        resumed_state = WorkflowRunner.resume_with_review(
            db=db,
            workflow_id=workflow_state["workflow_id"],
            reviewer="Chief Underwriting Officer",
            action="REJECT",
            justification="Rejected: Jurisdiction omission in NV introduces unfiled rate violation.",
        )
        assert resumed_state["status"] == "REJECTED"

        # Step 11 & 12: Simulate deployed transaction and run IntentGuard
        sim_input = {
            "jurisdiction": "NV",
            "driver_risk_score": 15,
            "vehicle_category": "SEDAN",
            "policy_active": True,
        }
        sim_observed_outcome = {
            "eligible": True,
            "discount_percentage": 10.0,
            "discount_code": "SAFE_DRIVER_10",
        }
        guard_res = IntentGuardVerifier.verify_event(
            db=db,
            transaction_id="TXN-E2E-ACCEPTANCE-01",
            input_data=sim_input,
            observed_outcome=sim_observed_outcome,
            reported_version_id="RULE-SAFE-DRIVER-v1.1-proposed",
            approved_reference_version_id="RULE-SAFE-DRIVER-v1.0",
            linked_change_id=cr.id,
        )

        # Step 13 & 14: Verify deviation finding created and traced
        assert guard_res["status"] == "DEVIATION"
        assert guard_res["is_deviation"] is True
        assert guard_res["finding_id"] is not None

        finding = db.query(Finding).filter_by(id=guard_res["finding_id"]).first()
        assert finding is not None
        assert finding.linked_change_id == cr.id
        assert finding.linked_rule_id == "RULE-SAFE-DRIVER"
        assert finding.linked_requirement_id == "REQ-AUTO-DISC-001"
        assert finding.linked_test_id == "TEST-SD-002"

        # Step 15: Inspect audit history
        audit_records = db.query(AuditEvent).all()
        assert len(audit_records) >= 3
        event_types = [a.event_type for a in audit_records]
        assert "WORKFLOW_STARTED" in event_types
        assert "HUMAN_REVIEW_REJECT" in event_types
        assert "INTENTGUARD_DEVIATION_DETECTED" in event_types

    finally:
        db.close()
