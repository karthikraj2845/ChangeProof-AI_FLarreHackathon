import pytest
from app.services.readiness_service import DeterministicReadinessPolicy


def test_readiness_policy_blocks_on_regression():
    test_summary = {
        "regressions": 1,
        "failed": 0,
        "regressions_detected": [{"test_id": "TEST-SD-002", "reason": "Accidental discount awarded in NV"}],
        "missing_coverage_tags": [],
    }
    impacted = [{"artifact_id": "ART-RULE-001", "confidence": 1.0}]

    verdict = DeterministicReadinessPolicy.evaluate(
        test_summary=test_summary,
        impacted_artifacts=impacted,
        baseline_version_id="RULE-SAFE-DRIVER-v1.0",
        proposed_version_id="RULE-SAFE-DRIVER-v1.1-proposed",
    )

    assert verdict["status"] == "BLOCKED"
    assert verdict["is_blocked"] is True
    assert len(verdict["blockers"]) > 0


def test_readiness_policy_passes_clean_release():
    test_summary = {
        "regressions": 0,
        "failed": 0,
        "regressions_detected": [],
        "missing_coverage_tags": [],
    }
    impacted = [{"artifact_id": "ART-RULE-001", "confidence": 1.0}]

    verdict = DeterministicReadinessPolicy.evaluate(
        test_summary=test_summary,
        impacted_artifacts=impacted,
        baseline_version_id="RULE-SAFE-DRIVER-v1.0",
        proposed_version_id="RULE-SAFE-DRIVER-v1.0",
    )

    assert verdict["status"] == "READY_FOR_REVIEW"
    assert verdict["is_blocked"] is False
    assert len(verdict["blockers"]) == 0
