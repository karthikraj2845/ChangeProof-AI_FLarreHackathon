import pytest
from app.db.session import SessionLocal
from app.testing.runner import RegressionTestRunner


def test_regression_test_runner_detects_seeded_defect():
    db = SessionLocal()
    try:
        test_ids = [
            "TEST-SD-001", "TEST-SD-002", "TEST-SD-003", "TEST-SD-004",
            "TEST-SD-005", "TEST-SD-006", "TEST-SD-007", "TEST-SD-008"
        ]
        res = RegressionTestRunner.run_tests(
            db=db,
            test_ids=test_ids,
            baseline_version_id="RULE-SAFE-DRIVER-v1.0",
            proposed_version_id="RULE-SAFE-DRIVER-v1.1-proposed",
        )

        assert res["total_executed"] == 8
        assert res["regressions"] >= 1, "Must detect at least 1 behavioral regression"

        # Check that TEST-SD-002 is the detected regression
        detected_ids = [r["test_id"] for r in res["regressions_detected"]]
        assert "TEST-SD-002" in detected_ids

        sd_002 = next(r for r in res["results"] if r["test_id"] == "TEST-SD-002")
        assert sd_002["status"] == "REGRESSION"
        assert sd_002["baseline_outcome"]["eligible"] is False
        assert sd_002["proposed_outcome"]["eligible"] is True
    finally:
        db.close()
