from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.change import ChangeRequest
from app.models.rule import RuleVersion
from app.models.snapshot import EvidenceSnapshot
from app.graph.service import InsuranceDependencyGraphService


class SnapshotService:
    """
    Constructs, hashes, persists, and verifies immutable evidence review snapshots.
    Guarantees that human reviews are bound to immutable, verifiable evidence.
    """

    @classmethod
    def compute_sha256(cls, data: Any) -> str:
        """Computes deterministic SHA-256 hash of any JSON-serializable Python data."""
        if isinstance(data, (dict, list)):
            serialized = json.dumps(data, sort_keys=True, default=str)
        else:
            serialized = str(data)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def compute_version_hash(cls, rule_definition: Dict[str, Any]) -> str:
        """Computes cryptographic content hash of a rule definition."""
        return cls.compute_sha256(rule_definition)

    @classmethod
    def create_snapshot(
        cls,
        db: Session,
        change_request_id: str,
        workflow_run_id: Optional[str],
        target_rule_id: str,
        baseline_version_id: str,
        proposed_version_id: str,
        test_summary: Dict[str, Any],
        impacted_artifacts: List[Dict[str, Any]],
        selected_test_ids: List[str],
        readiness_result: Dict[str, Any],
        test_provenance: Optional[Dict[str, Any]] = None,
    ) -> EvidenceSnapshot:
        """
        Constructs an immutable EvidenceSnapshot, calculates its cryptographic hash,
        and saves it to the database.
        """
        baseline_rv = db.query(RuleVersion).filter_by(id=baseline_version_id).first()
        proposed_rv = db.query(RuleVersion).filter_by(id=proposed_version_id).first()

        baseline_hash = cls.compute_version_hash(baseline_rv.rule_definition) if baseline_rv else "UNKNOWN_BASELINE"
        proposed_hash = cls.compute_version_hash(proposed_rv.rule_definition) if proposed_rv else "UNKNOWN_PROPOSED"

        graph_svc = InsuranceDependencyGraphService(db)
        graph_fingerprint = graph_svc.get_graph_fingerprint()

        now = datetime.now(timezone.utc)
        impacted_ids = [art.get("artifact_id") for art in impacted_artifacts if art.get("artifact_id")]

        # Assemble full canonical snapshot data dictionary
        snapshot_payload = {
            "change_request_id": change_request_id,
            "workflow_run_id": workflow_run_id,
            "target_rule_id": target_rule_id,
            "baseline_version_id": baseline_version_id,
            "baseline_version_hash": baseline_hash,
            "proposed_version_id": proposed_version_id,
            "proposed_version_hash": proposed_hash,
            "graph_fingerprint": graph_fingerprint,
            "selected_test_ids": sorted(selected_test_ids),
            "test_provenance": test_provenance or {},
            "impacted_artifact_ids": sorted(impacted_ids),
            "test_summary": {
                "total_executed": test_summary.get("total_executed", 0),
                "passed": test_summary.get("passed", 0),
                "failed": test_summary.get("failed", 0),
                "regressions": test_summary.get("regressions", 0),
                "missing_coverage_tags": sorted(test_summary.get("missing_coverage_tags") or []),
            },
            "readiness_status": readiness_result.get("status", "UNKNOWN"),
            "is_blocked": readiness_result.get("is_blocked", False),
            "blockers": readiness_result.get("blockers", []),
            "created_at": now.isoformat(),
        }

        full_hash = cls.compute_sha256(snapshot_payload)
        snapshot_id = f"SNAP-{full_hash[:12].upper()}"

        # Check if identical snapshot already exists
        existing = db.query(EvidenceSnapshot).filter_by(snapshot_hash=full_hash).first()
        if existing:
            return existing

        snapshot = EvidenceSnapshot(
            id=snapshot_id,
            change_request_id=change_request_id,
            workflow_run_id=workflow_run_id,
            target_rule_id=target_rule_id,
            baseline_version_id=baseline_version_id,
            baseline_version_hash=baseline_hash,
            proposed_version_id=proposed_version_id,
            proposed_version_hash=proposed_hash,
            graph_fingerprint=graph_fingerprint,
            snapshot_hash=full_hash,
            readiness_status=readiness_result.get("status", "UNKNOWN"),
            is_blocked=readiness_result.get("is_blocked", False),
            test_summary=test_summary,
            selected_test_ids=sorted(selected_test_ids),
            impacted_artifact_ids=sorted(impacted_ids),
            full_snapshot_data=snapshot_payload,
            created_at=now,
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    @classmethod
    def verify_snapshot_validity(
        cls,
        db: Session,
        snapshot_id: str,
        expected_workflow_run_id: Optional[str] = None,
        expected_change_request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validates that an existing snapshot is cryptographically intact and has not become stale.
        Checks:
          1. Snapshot exists and its data reproduces the snapshot_hash.
          2. Snapshot belongs to the expected workflow run / change request.
          3. Baseline rule version has not changed.
          4. Proposed rule version has not changed.
          5. Graph dependencies have not changed (graph_fingerprint matches).
        """
        snapshot = db.query(EvidenceSnapshot).filter_by(id=snapshot_id).first()
        if not snapshot:
            return {"valid": False, "stale": False, "reason": f"Snapshot '{snapshot_id}' does not exist."}

        # Validate workflow / change isolation
        if expected_workflow_run_id and snapshot.workflow_run_id and snapshot.workflow_run_id != expected_workflow_run_id:
            return {
                "valid": False,
                "stale": False,
                "reason": f"Cross-run collision: Snapshot '{snapshot_id}' belongs to workflow '{snapshot.workflow_run_id}', not '{expected_workflow_run_id}'.",
            }
        if expected_change_request_id and snapshot.change_request_id != expected_change_request_id:
            return {
                "valid": False,
                "stale": False,
                "reason": f"Cross-change collision: Snapshot '{snapshot_id}' belongs to change '{snapshot.change_request_id}', not '{expected_change_request_id}'.",
            }

        # 1. Verify snapshot hash integrity
        recomputed_hash = cls.compute_sha256(snapshot.full_snapshot_data)
        if recomputed_hash != snapshot.snapshot_hash:
            return {
                "valid": False,
                "stale": False,
                "reason": f"Tampered snapshot detected! Recomputed hash does not match stored hash.",
            }

        # 2. Check baseline version immutability
        baseline_rv = db.query(RuleVersion).filter_by(id=snapshot.baseline_version_id).first()
        if not baseline_rv:
            return {"valid": False, "stale": True, "reason": "Baseline rule version no longer exists."}
        current_baseline_hash = cls.compute_version_hash(baseline_rv.rule_definition)
        if current_baseline_hash != snapshot.baseline_version_hash:
            return {
                "valid": False,
                "stale": True,
                "reason": f"Baseline rule version has mutated since snapshot was taken. Fresh review required.",
            }

        # 3. Check proposed version immutability
        proposed_rv = db.query(RuleVersion).filter_by(id=snapshot.proposed_version_id).first()
        if not proposed_rv:
            return {"valid": False, "stale": True, "reason": "Proposed rule version no longer exists."}
        current_proposed_hash = cls.compute_version_hash(proposed_rv.rule_definition)
        if current_proposed_hash != snapshot.proposed_version_hash:
            return {
                "valid": False,
                "stale": True,
                "reason": f"Proposed rule version content has mutated since snapshot was taken. Fresh review required.",
            }

        # 4. Check graph fingerprint
        graph_svc = InsuranceDependencyGraphService(db)
        current_fingerprint = graph_svc.get_graph_fingerprint()
        if current_fingerprint != snapshot.graph_fingerprint:
            return {
                "valid": False,
                "stale": True,
                "reason": "Underlying dependency graph topology has changed since snapshot was created. Re-analysis required.",
            }

        return {
            "valid": True,
            "stale": False,
            "snapshot_id": snapshot.id,
            "snapshot_hash": snapshot.snapshot_hash,
            "is_blocked": snapshot.is_blocked,
            "readiness_status": snapshot.readiness_status,
        }
