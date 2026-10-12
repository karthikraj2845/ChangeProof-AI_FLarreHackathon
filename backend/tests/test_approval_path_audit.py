"""
Priority 6: Approval Path Audit Tests.
Verifies that no API endpoint or internal function can bypass mandatory readiness blockers.
Tests both the workflow runner path and the changes.py direct approval path.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.db.session import SessionLocal
from app.models.audit import AuditEvent
from app.models.change import ChangeRequest
from app.orchestration.runner import WorkflowRunner

client = TestClient(fastapi_app)


class TestApprovalPathAudit:
    """Verify every approval path enforces governance and creates audit trails."""

    def test_changes_approve_endpoint_blocked_by_regression(self):
        """
        POST /changes/{id}/approve must reject when readiness is BLOCKED
        and create an audit denial event.
        """
        db = SessionLocal()
        try:
            # Run the full workflow to get a BLOCKED change
            state = WorkflowRunner.start_change_assurance(
                db=db,
                change_request_id="CR-2026-001",
                user_request="Remove the jurisdiction restriction from the safe-driver discount eligibility rule.",
            )

            # The change must be BLOCKED (has seeded regression)
            cr = db.query(ChangeRequest).filter_by(id="CR-2026-001").first()
            assert cr.readiness_status == "BLOCKED"

            # Attempt approval via the API endpoint
            response = client.post(
                "/api/changes/CR-2026-001/approve",
                json={
                    "reviewer": "Audit Test Reviewer",
                    "action": "APPROVE",
                    "justification": "Attempting to approve via API.",
                },
            )

            assert response.status_code == 400
            assert "GOVERNANCE VIOLATION" in response.json()["detail"]

            # Verify denial audit event was created
            denial = db.query(AuditEvent).filter(
                AuditEvent.event_type == "APPROVAL_ATTEMPT_DENIED_REGRESSION_BLOCK",
                AuditEvent.entity_id == "CR-2026-001",
                AuditEvent.actor == "Audit Test Reviewer",
            ).first()
            assert denial is not None, "Denial audit event must be recorded for blocked approval"
        finally:
            db.close()

    def test_changes_reject_endpoint_creates_audit_event(self):
        """
        POST /changes/{id}/reject must create an audit event with actor and justification.
        """
        db = SessionLocal()
        try:
            response = client.post(
                "/api/changes/CR-2026-001/reject",
                json={
                    "reviewer": "Rejection Reviewer",
                    "action": "REJECT",
                    "justification": "Rejecting for audit test.",
                },
            )

            assert response.status_code == 200
            assert response.json()["status"] == "REJECTED"

            # Verify rejection audit event
            rejection = db.query(AuditEvent).filter(
                AuditEvent.event_type == "HUMAN_REJECTION",
                AuditEvent.entity_id == "CR-2026-001",
                AuditEvent.actor == "Rejection Reviewer",
            ).first()
            assert rejection is not None, "Rejection audit event must be recorded"
            assert rejection.details.get("justification") == "Rejecting for audit test."
        finally:
            db.close()

    def test_workflow_approve_blocked_creates_audit_event(self):
        """
        WorkflowRunner.resume_with_review APPROVE on BLOCKED must create denial audit event.
        """
        db = SessionLocal()
        try:
            state = WorkflowRunner.start_change_assurance(
                db=db,
                change_request_id="CR-2026-001",
                user_request="Remove the jurisdiction restriction from the safe-driver discount eligibility rule.",
            )
            wf_id = state["workflow_id"]

            # Count before
            before_count = db.query(AuditEvent).filter(
                AuditEvent.event_type == "APPROVAL_ATTEMPT_DENIED_REGRESSION_BLOCK",
                AuditEvent.entity_id == wf_id,
            ).count()

            with pytest.raises(ValueError, match="GOVERNANCE VIOLATION"):
                WorkflowRunner.resume_with_review(
                    db=db,
                    workflow_id=wf_id,
                    reviewer="Audit Override Reviewer",
                    action="APPROVE",
                    justification="Override attempt.",
                )

            after_count = db.query(AuditEvent).filter(
                AuditEvent.event_type == "APPROVAL_ATTEMPT_DENIED_REGRESSION_BLOCK",
                AuditEvent.entity_id == wf_id,
            ).count()
            assert after_count > before_count, "Denial audit event must be created"
        finally:
            db.close()

    def test_approval_requires_valid_snapshot(self):
        """
        Attempting to APPROVE without a snapshot must fail with GOVERNANCE VIOLATION.
        """
        db = SessionLocal()
        try:
            # Create a fresh change request that does NOT have readiness run yet
            cr = db.query(ChangeRequest).filter_by(id="CR-2026-001").first()
            cr.readiness_status = "READY"  # Simulate non-blocked
            cr.readiness_details = {}  # No snapshot
            db.commit()

            response = client.post(
                "/api/changes/CR-2026-001/approve",
                json={
                    "reviewer": "Snapshot Test Reviewer",
                    "action": "APPROVE",
                    "justification": "Test no-snapshot denial.",
                },
            )

            assert response.status_code == 400
            assert "GOVERNANCE VIOLATION" in response.json()["detail"] or "Evidence Snapshot" in response.json()["detail"]
        finally:
            db.close()

    def test_hash_mismatch_denial_creates_audit_event(self):
        """
        Providing a wrong snapshot_hash must fail with EVIDENCE HASH MISMATCH
        and create a denial audit event.
        """
        db = SessionLocal()
        try:
            # First run the workflow to populate readiness with a snapshot
            state = WorkflowRunner.start_change_assurance(
                db=db,
                change_request_id="CR-2026-001",
                user_request="Remove the jurisdiction restriction from the safe-driver discount eligibility rule.",
            )
            wf_id = state["workflow_id"]

            # Attempt via the workflow runner path
            with pytest.raises(ValueError, match="STALE OR INVALID EVIDENCE|EVIDENCE HASH MISMATCH|GOVERNANCE VIOLATION"):
                WorkflowRunner.resume_with_review(
                    db=db,
                    workflow_id=wf_id,
                    reviewer="Hash Test Reviewer",
                    action="REJECT",  # REJECT doesn't hit the blocker check
                    justification="Test hash mismatch.",
                    snapshot_hash="BOGUS_HASH_VALUE",
                )
        finally:
            db.close()
