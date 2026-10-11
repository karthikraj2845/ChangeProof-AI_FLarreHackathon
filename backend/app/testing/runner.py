import time
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.rule import RuleVersion
from app.models.test import RegressionTest, TestResult, VerificationRun
from app.rules.engine import DeterministicRuleEngine


class RegressionTestRunner:
    """
    Executes deterministic baseline vs proposed regression tests.
    Identifies behavioral regressions, failures, and coverage completeness.
    """

    @classmethod
    def run_tests(
        cls,
        db: Session,
        test_ids: List[str],
        baseline_version_id: str,
        proposed_version_id: str,
        verification_run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        baseline_rv = db.query(RuleVersion).filter_by(id=baseline_version_id).first()
        proposed_rv = db.query(RuleVersion).filter_by(id=proposed_version_id).first()

        if not baseline_rv or not proposed_rv:
            raise ValueError(f"Rule versions {baseline_version_id} or {proposed_version_id} not found.")

        tests = db.query(RegressionTest).filter(RegressionTest.id.in_(test_ids)).all()
        # Preserve input order or sort
        tests = sorted(tests, key=lambda t: test_ids.index(t.id) if t.id in test_ids else 999)

        results: List[Dict[str, Any]] = []
        regressions_detected: List[Dict[str, Any]] = []
        passed_count = 0
        failed_count = 0
        regression_count = 0
        covered_tags: set = set()

        for test in tests:
            start_t = time.perf_counter()

            # 1. Evaluate baseline version
            base_eval = DeterministicRuleEngine.evaluate(
                baseline_rv.rule_definition,
                test.input_data,
                version_id=baseline_version_id
            )

            # 2. Evaluate proposed version
            prop_eval = DeterministicRuleEngine.evaluate(
                proposed_rv.rule_definition,
                test.input_data,
                version_id=proposed_version_id
            )

            elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)

            for tag in (test.coverage_tags or []):
                covered_tags.add(tag)

            # 3. Determine status and regression
            is_regression = False
            status = "PASSED"
            failure_reason = None

            # Detect behavioral regression:
            # Baseline rejected/disallowed discount, but proposed version allowed it (unexpected behavioral shift)
            if not base_eval.eligible and prop_eval.eligible:
                is_regression = True
                status = "REGRESSION"
                regression_count += 1
                failure_reason = (
                    f"CRITICAL BEHAVIORAL REGRESSION: Input '{test.name}' was NOT eligible under baseline {baseline_version_id} "
                    f"(0% discount), but incorrectly qualified under proposed {proposed_version_id} "
                    f"with {prop_eval.discount_percentage}% discount! Reason: {prop_eval.explanation}"
                )
                regressions_detected.append({
                    "test_id": test.id,
                    "test_name": test.name,
                    "reason": failure_reason,
                    "input_data": test.input_data,
                    "baseline_outcome": base_eval.model_dump(),
                    "proposed_outcome": prop_eval.model_dump(),
                })
            elif test.expected_baseline_outcome.get("eligible") != base_eval.eligible:
                status = "FAILED"
                failed_count += 1
                failure_reason = f"Baseline outcome mismatch with expected specification."
            else:
                passed_count += 1

            result_entry = {
                "test_id": test.id,
                "name": test.name,
                "category": test.category,
                "input_data": test.input_data,
                "expected_outcome": test.expected_baseline_outcome,
                "baseline_outcome": {
                    "eligible": base_eval.eligible,
                    "discount_percentage": base_eval.discount_percentage,
                    "discount_code": base_eval.discount_code,
                    "explanation": base_eval.explanation,
                },
                "proposed_outcome": {
                    "eligible": prop_eval.eligible,
                    "discount_percentage": prop_eval.discount_percentage,
                    "discount_code": prop_eval.discount_code,
                    "explanation": prop_eval.explanation,
                },
                "status": status,
                "is_regression": is_regression,
                "failure_reason": failure_reason,
                "latency_ms": elapsed_ms,
                "coverage_tags": test.coverage_tags,
            }
            results.append(result_entry)

            # Persist test result if verification run ID is provided
            if verification_run_id:
                tr = TestResult(
                    id=f"TR-{verification_run_id[:8]}-{test.id}",
                    verification_run_id=verification_run_id,
                    test_id=test.id,
                    rule_version_id=proposed_version_id,
                    expected_outcome=test.expected_baseline_outcome,
                    actual_outcome=result_entry["proposed_outcome"],
                    status=status,
                    failure_reason=failure_reason,
                    execution_latency_ms=elapsed_ms,
                )
                db.add(tr)

        if verification_run_id:
            db.commit()

        # Mandatory coverage tags for auto underwriting rules
        mandatory_tags = {"jurisdiction", "driver_risk_score", "vehicle_category", "policy_active", "unsupported_state"}
        missing_coverage = list(mandatory_tags - covered_tags)

        return {
            "total_executed": len(tests),
            "passed": passed_count,
            "failed": failed_count,
            "regressions": regression_count,
            "results": results,
            "regressions_detected": regressions_detected,
            "covered_tags": list(covered_tags),
            "missing_coverage_tags": missing_coverage,
            "has_coverage_gaps": len(missing_coverage) > 0,
        }
