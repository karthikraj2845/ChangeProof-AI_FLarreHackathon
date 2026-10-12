"""
Priority 5 Tests: IntentGuard traceability and UNVERIFIABLE provenance verification.
Ensures that requirement and test links use explicit verified relationships,
and returns UNVERIFIABLE when no reliable traceability is available.
"""
import pytest
from app.db.session import SessionLocal
from app.models.finding import Finding
from app.models.test import RegressionTest
from app.verification.intent_guard import IntentGuardVerifier


class TestIntentGuardTraceability:
    """Validate that IntentGuard uses explicit verified relationships only."""

    def test_deviation_finding_has_verified_requirement_provenance(self):
        """
        When a deviation is detected for NV (which has tests with linked_requirement_id),
        the finding's evidence must show VERIFIED_VIA_TEST_LINK provenance.
        """
        db = SessionLocal()
        try:
            res = IntentGuardVerifier.verify_event(
                db=db,
                transaction_id="TXN-PROV-NV-001",
                input_data={
                    "jurisdiction": "NV",
                    "driver_risk_score": 15,
                    "vehicle_category": "SEDAN",
                    "policy_active": True,
                },
                observed_outcome={
                    "eligible": True,
                    "discount_percentage": 10.0,
                    "discount_code": "SAFE_DRIVER_10",
                },
                reported_version_id="RULE-SAFE-DRIVER-v1.1-proposed",
                approved_reference_version_id="RULE-SAFE-DRIVER-v1.0",
                linked_change_id="CR-2026-001",
            )

            assert res["status"] == "DEVIATION"
            assert res["finding_id"] is not None

            # Verify finding persisted with correct traceability provenance
            finding = db.query(Finding).filter_by(id=res["finding_id"]).first()
            assert finding is not None
            assert finding.linked_requirement_id == "REQ-AUTO-DISC-001"

            # Verify evidence includes provenance metadata
            evidence = finding.evidence
            assert "traceability" in evidence
            assert evidence["traceability"]["requirement_provenance"] == "VERIFIED_VIA_TEST_LINK"
        finally:
            db.close()

    def test_deviation_finding_has_verified_test_provenance_for_matching_jurisdiction(self):
        """
        For NV jurisdiction input, a test with matching NV jurisdiction must be linked
        with VERIFIED_SCENARIO_MATCH provenance.
        """
        db = SessionLocal()
        try:
            res = IntentGuardVerifier.verify_event(
                db=db,
                transaction_id="TXN-PROV-NV-002",
                input_data={
                    "jurisdiction": "NV",
                    "driver_risk_score": 15,
                    "vehicle_category": "SEDAN",
                    "policy_active": True,
                },
                observed_outcome={
                    "eligible": True,
                    "discount_percentage": 10.0,
                },
                reported_version_id="RULE-SAFE-DRIVER-v1.1-proposed",
                approved_reference_version_id="RULE-SAFE-DRIVER-v1.0",
            )

            assert res["status"] == "DEVIATION"

            finding = db.query(Finding).filter_by(id=res["finding_id"]).first()
            evidence = finding.evidence

            assert evidence["traceability"]["test_provenance"] == "VERIFIED_SCENARIO_MATCH"
            # The linked test must have NV in its input
            assert finding.linked_test_id is not None

            linked_test = db.query(RegressionTest).filter_by(id=finding.linked_test_id).first()
            assert linked_test is not None
            assert linked_test.input_data.get("jurisdiction") == "NV"
        finally:
            db.close()

    def test_unverifiable_test_provenance_for_unmatched_jurisdiction(self):
        """
        For a jurisdiction not matching any test's input (e.g., WY — not in any seeded test),
        the finding must have linked_test_id=None and UNVERIFIABLE test provenance.
        WY is also NOT in the approved jurisdiction list for v1.0, so the expected outcome
        from the approved reference is 0% (not eligible), creating a deviation with the
        observed 10%.
        """
        db = SessionLocal()
        try:
            # WY is not in the approved jurisdiction list AND not in any seeded test input_data
            res = IntentGuardVerifier.verify_event(
                db=db,
                transaction_id="TXN-PROV-WY-001",
                input_data={
                    "jurisdiction": "WY",
                    "driver_risk_score": 15,
                    "vehicle_category": "SEDAN",
                    "policy_active": True,
                },
                observed_outcome={
                    "eligible": True,
                    "discount_percentage": 10.0,
                },
                reported_version_id="RULE-SAFE-DRIVER-v1.1-proposed",
                approved_reference_version_id="RULE-SAFE-DRIVER-v1.0",
            )

            assert res["status"] == "DEVIATION"

            finding = db.query(Finding).filter_by(id=res["finding_id"]).first()
            evidence = finding.evidence

            # Test provenance must be UNVERIFIABLE — no seeded test has TX jurisdiction
            assert evidence["traceability"]["test_provenance"] == "UNVERIFIABLE"
            assert finding.linked_test_id is None
        finally:
            db.close()

    def test_verified_event_returns_no_finding(self):
        """
        When observed outcome matches expected, status is VERIFIED with no finding.
        """
        db = SessionLocal()
        try:
            res = IntentGuardVerifier.verify_event(
                db=db,
                transaction_id="TXN-PROV-CA-MATCH",
                input_data={
                    "jurisdiction": "CA",
                    "driver_risk_score": 15,
                    "vehicle_category": "SEDAN",
                    "policy_active": True,
                },
                observed_outcome={
                    "eligible": True,
                    "discount_percentage": 10.0,
                },
                reported_version_id="RULE-SAFE-DRIVER-v1.0",
                approved_reference_version_id="RULE-SAFE-DRIVER-v1.0",
            )

            assert res["status"] == "VERIFIED"
            assert res["is_deviation"] is False
            assert res["finding_id"] is None
        finally:
            db.close()

    def test_unapproved_reference_version_returns_unverifiable(self):
        """
        An unapproved reference version must return UNVERIFIABLE status.
        """
        db = SessionLocal()
        try:
            res = IntentGuardVerifier.verify_event(
                db=db,
                transaction_id="TXN-UNVERIF-001",
                input_data={
                    "jurisdiction": "CA",
                    "driver_risk_score": 15,
                    "vehicle_category": "SEDAN",
                    "policy_active": True,
                },
                observed_outcome={
                    "eligible": True,
                    "discount_percentage": 10.0,
                },
                reported_version_id="RULE-SAFE-DRIVER-v1.1-proposed",
                # proposed version is not APPROVED, so verification should fail
                approved_reference_version_id="RULE-SAFE-DRIVER-v1.1-proposed",
            )

            assert res["status"] == "UNVERIFIABLE"
            assert "NOT 'APPROVED'" in res["summary"] or "not found" in res["summary"].lower()
        finally:
            db.close()
