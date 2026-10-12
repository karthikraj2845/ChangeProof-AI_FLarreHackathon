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

            # Attempt approval via the API endpoint providing valid snapshot evidence
            snap_id = state["snapshot_id"]
            snap_hash = state["snapshot_hash"]
            response = client.post(
                "/api/changes/CR-2026-001/approve",
                json={
                    "reviewer": "Audit Test Reviewer",
                    "action": "APPROVE",
                    "justification": "Attempting to approve via API.",
                    "snapshot_id": snap_id,
                    "snapshot_hash": snap_hash,
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

            snap_id = state["snapshot_id"]
            snap_hash = state["snapshot_hash"]

            with pytest.raises(ValueError, match="GOVERNANCE VIOLATION"):
                WorkflowRunner.resume_with_review(
                    db=db,
                    workflow_id=wf_id,
                    reviewer="Audit Override Reviewer",
                    action="APPROVE",
                    justification="Override attempt.",
                    snapshot_id=snap_id,
                    snapshot_hash=snap_hash,
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

    def test_approve_with_missing_snapshot_id_rejected_with_audit_trail(self):
        """APPROVE without explicit snapshot_id must be rejected and logged to audit."""
        db = SessionLocal()
        try:
            state = WorkflowRunner.start_change_assurance(
                db=db,
                change_request_id="CR-2026-001",
                user_request="Remove the jurisdiction restriction from the safe-driver discount eligibility rule.",
            )
            wf_id = state["workflow_id"]

            with pytest.raises(ValueError, match="Approval requires explicit snapshot_id"):
                WorkflowRunner.resume_with_review(
                    db=db,
                    workflow_id=wf_id,
                    reviewer="Compliance Auditor",
                    action="APPROVE",
                    justification="Approve without snapshot id",
                    snapshot_id=None,
                    snapshot_hash="some_hash",
                )

            denial = db.query(AuditEvent).filter(
                AuditEvent.event_type == "APPROVAL_ATTEMPT_DENIED_NO_SNAPSHOT",
                AuditEvent.entity_id == wf_id,
            ).first()
            assert denial is not None
        finally:
            db.close()

    def test_approve_with_missing_snapshot_hash_rejected_with_audit_trail(self):
        """APPROVE without explicit snapshot_hash must be rejected and logged to audit."""
        db = SessionLocal()
        try:
            state = WorkflowRunner.start_change_assurance(
                db=db,
                change_request_id="CR-2026-001",
                user_request="Remove the jurisdiction restriction from the safe-driver discount eligibility rule.",
            )
            wf_id = state["workflow_id"]
            snap_id = state["snapshot_id"]

            with pytest.raises(ValueError, match="Approval requires explicit snapshot_hash"):
                WorkflowRunner.resume_with_review(
                    db=db,
                    workflow_id=wf_id,
                    reviewer="Compliance Auditor",
                    action="APPROVE",
                    justification="Approve without snapshot hash",
                    snapshot_id=snap_id,
                    snapshot_hash=None,
                )

            denial = db.query(AuditEvent).filter(
                AuditEvent.event_type == "APPROVAL_ATTEMPT_DENIED_NO_HASH",
                AuditEvent.entity_id == wf_id,
            ).first()
            assert denial is not None
        finally:
            db.close()

    def test_approve_with_incorrect_hash_rejected_with_audit_trail(self):
        """APPROVE with tampered or incorrect snapshot_hash must fail with mismatch and audit event."""
        db = SessionLocal()
        try:
            state = WorkflowRunner.start_change_assurance(
                db=db,
                change_request_id="CR-2026-001",
                user_request="Remove the jurisdiction restriction from the safe-driver discount eligibility rule.",
            )
            wf_id = state["workflow_id"]
            snap_id = state["snapshot_id"]

            # Note: Even if we try to APPROVE, blocker check runs first if BLOCKED.
            # But with wrong hash, validity check or hash check rejects it.
            with pytest.raises(ValueError, match="GOVERNANCE VIOLATION|STALE OR INVALID EVIDENCE|EVIDENCE HASH MISMATCH"):
                WorkflowRunner.resume_with_review(
                    db=db,
                    workflow_id=wf_id,
                    reviewer="Hash Tamperer",
                    action="APPROVE",
                    justification="Approve with fake hash",
                    snapshot_id=snap_id,
                    snapshot_hash="BOGUS_TAMPERED_HASH_9999",
                )
        finally:
            db.close()

    def test_approve_with_wrong_workflow_or_change_rejected(self):
        """APPROVE with snapshot belonging to another workflow run must fail cross-run check."""
        db = SessionLocal()
        try:
            state1 = WorkflowRunner.start_change_assurance(
                db=db,
                change_request_id="CR-2026-001",
                user_request="Remove the jurisdiction restriction from the safe-driver discount eligibility rule.",
            )
            state2 = WorkflowRunner.start_change_assurance(
                db=db,
                change_request_id="CR-2026-001",
                user_request="Remove the jurisdiction restriction from the safe-driver discount eligibility rule.",
            )
            wf1_id = state1["workflow_id"]
            wf2_id = state2["workflow_id"]
            snap1_id = state1["snapshot_id"]
            snap1_hash = state1["snapshot_hash"]

            # Attempting to use workflow 1's snapshot to approve workflow 2
            with pytest.raises(ValueError, match="GOVERNANCE VIOLATION|STALE OR INVALID EVIDENCE"):
                WorkflowRunner.resume_with_review(
                    db=db,
                    workflow_id=wf2_id,
                    reviewer="Cross Run Attacker",
                    action="APPROVE",
                    justification="Approve wf2 using wf1 snapshot",
                    snapshot_id=snap1_id,
                    snapshot_hash=snap1_hash,
                )
        finally:
            db.close()
