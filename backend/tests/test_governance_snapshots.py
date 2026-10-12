import pytest
from app.db.session import SessionLocal
from app.models.change import ChangeRequest
from app.models.rule import RuleVersion
from app.services.snapshot_service import SnapshotService
from app.services.readiness_service import DeterministicReadinessPolicy


def test_immutable_snapshot_creation_and_integrity():
    db = SessionLocal()
    try:
        cr = db.query(ChangeRequest).filter_by(id="CR-2026-001").first()
        assert cr is not None

        test_summary = {
            "total_executed": 8,
            "passed": 7,
            "failed": 0,
            "regressions": 1,
            "missing_coverage_tags": [],
        }

        readiness = DeterministicReadinessPolicy.evaluate(
            test_summary=test_summary,
            impacted_artifacts=[],
            baseline_version_id=cr.baseline_version_id,
            proposed_version_id=cr.proposed_version_id,
        )

        snapshot = SnapshotService.create_snapshot(
            db=db,
            change_request_id=cr.id,
            workflow_run_id="WF-GOV-TEST",
            target_rule_id=cr.target_rule_id,
            baseline_version_id=cr.baseline_version_id,
            proposed_version_id=cr.proposed_version_id,
            test_summary=test_summary,
            impacted_artifacts=[],
            selected_test_ids=["TEST-SD-001", "TEST-SD-002"],
            readiness_result=readiness,
        )

        assert snapshot.id.startswith("SNAP-")
        assert len(snapshot.snapshot_hash) == 64

        # Validate integrity
        val = SnapshotService.verify_snapshot_validity(db, snapshot.id)
        assert val["valid"] is True
        assert val["stale"] is False
    finally:
        db.close()


def test_stale_evidence_detection_on_mutated_version():
    db = SessionLocal()
    try:
        cr = db.query(ChangeRequest).filter_by(id="CR-2026-001").first()
        snapshot = db.query(SnapshotService.create_snapshot(
            db=db,
            change_request_id=cr.id,
            workflow_run_id="WF-STALE-TEST",
            target_rule_id=cr.target_rule_id,
            baseline_version_id=cr.baseline_version_id,
            proposed_version_id=cr.proposed_version_id,
            test_summary={"total_executed": 8, "regressions": 0},
            impacted_artifacts=[],
            selected_test_ids=["TEST-SD-001"],
            readiness_result={"status": "READY_FOR_REVIEW", "is_blocked": False},
        ).__class__).filter_by(change_request_id=cr.id).first()

        # Artificially alter the snapshot's baseline hash to simulate version mutation
        original_hash = snapshot.baseline_version_hash
        snapshot.baseline_version_hash = "MUTATED_HASH_1234567890abcdef"
        db.commit()

        # Check validity: should detect stale/tampered version
        val = SnapshotService.verify_snapshot_validity(db, snapshot.id)
        assert val["valid"] is False
        assert val["stale"] is True
        assert "Baseline rule version has mutated" in val["reason"]

        # Restore
        snapshot.baseline_version_hash = original_hash
        db.commit()
    finally:
        db.close()


def test_tampered_snapshot_payload_detection():
    db = SessionLocal()
    try:
        cr = db.query(ChangeRequest).filter_by(id="CR-2026-001").first()
        snapshot = SnapshotService.create_snapshot(
            db=db,
            change_request_id=cr.id,
            workflow_run_id="WF-TAMPER-TEST",
            target_rule_id=cr.target_rule_id,
            baseline_version_id=cr.baseline_version_id,
            proposed_version_id=cr.proposed_version_id,
            test_summary={"total_executed": 8, "regressions": 0},
            impacted_artifacts=[],
            selected_test_ids=["TEST-SD-001"],
            readiness_result={"status": "READY_FOR_REVIEW", "is_blocked": False},
        )

        # Alter the stored hash directly to simulate tampering
        original_hash = snapshot.snapshot_hash
        snapshot.snapshot_hash = "f" * 64
        db.commit()

        val = SnapshotService.verify_snapshot_validity(db, snapshot.id)
        assert val["valid"] is False
        assert "Tampered snapshot detected" in val["reason"]

        # Restore
        snapshot.snapshot_hash = original_hash
        db.commit()
    finally:
        db.close()
