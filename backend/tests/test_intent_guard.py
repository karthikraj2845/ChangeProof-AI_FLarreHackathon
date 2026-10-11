import pytest
from app.db.session import SessionLocal
from app.models.finding import Finding
from app.verification.intent_guard import IntentGuardVerifier


def test_intent_guard_detects_deviation_and_creates_finding():
    db = SessionLocal()
    try:
        txn_id = "TXN-TEST-NV-99"
        input_data = {
            "jurisdiction": "NV",
            "driver_risk_score": 15,
            "vehicle_category": "SEDAN",
            "policy_active": True,
        }
        # Observed deployed outcome (from defective proposed version v1.1)
        observed_outcome = {
            "eligible": True,
            "discount_percentage": 10.0,
            "discount_code": "SAFE_DRIVER_10",
        }

        res = IntentGuardVerifier.verify_event(
            db=db,
            transaction_id=txn_id,
            input_data=input_data,
            observed_outcome=observed_outcome,
            reported_version_id="RULE-SAFE-DRIVER-v1.1-proposed",
            approved_reference_version_id="RULE-SAFE-DRIVER-v1.0",
            linked_change_id="CR-2026-001",
        )

        assert res["status"] == "DEVIATION"
        assert res["is_deviation"] is True
        assert res["finding_id"] is not None

        # Verify persisted finding
        finding = db.query(Finding).filter_by(id=res["finding_id"]).first()
        assert finding is not None
        assert finding.finding_type == "DEVIATION"
        assert finding.severity == "CRITICAL"
        assert finding.linked_change_id == "CR-2026-001"
        assert finding.linked_requirement_id == "REQ-AUTO-DISC-001"
    finally:
        db.close()
