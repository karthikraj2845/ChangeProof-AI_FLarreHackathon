from typing import Any, Dict, List, Optional


class DeterministicReadinessPolicy:
    """
    Deterministic release-readiness policy engine.
    Evaluates evidence completeness, regressions, and coverage constraints.
    LLM agents CANNOT override these policy verdicts.
    """

    @classmethod
    def evaluate(
        cls,
        test_summary: Dict[str, Any],
        impacted_artifacts: List[Dict[str, Any]],
        baseline_version_id: Optional[str] = None,
        proposed_version_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        blockers: List[str] = []
        warnings: List[str] = []
        human_review_triggers: List[str] = []

        # 1. Version provenance check
        if not baseline_version_id or not proposed_version_id:
            blockers.append("Missing required baseline or proposed rule version identifier.")

        # 2. Critical Regression check
        regressions = test_summary.get("regressions", 0)
        if regressions > 0:
            blockers.append(
                f"BLOCKED BY REGRESSION: Detected {regressions} behavioral regression(s) where proposed rule allowed "
                f"unapproved outcomes disallowed by baseline."
            )
            for reg in test_summary.get("regressions_detected", []):
                blockers.append(f"  - [{reg.get('test_id')}]: {reg.get('reason')}")

        # 3. Test execution failures
        failed = test_summary.get("failed", 0)
        if failed > 0:
            blockers.append(f"BLOCKED BY TEST FAILURE: {failed} test(s) failed against baseline specification.")

        # 4. Mandatory coverage gaps
        missing_tags = test_summary.get("missing_coverage_tags", [])
        if missing_tags:
            warnings.append(f"Coverage gap: missing mandatory scenario tags: {', '.join(missing_tags)}")
            human_review_triggers.append(f"Unverified underwriting scenarios: {', '.join(missing_tags)}")

        # 5. Dependency uncertainty
        for art in impacted_artifacts:
            confidence = art.get("confidence", 1.0)
            if confidence < 0.70:
                warnings.append(f"Low confidence ({confidence:.0%}) dependency edge detected on artifact {art.get('artifact_id')}.")
                human_review_triggers.append(f"Uncertain dependency: {art.get('name')} (confidence {confidence:.0%})")

        # 6. Determine final readiness status
        if blockers:
            status = "BLOCKED"
            recommendation = (
                "Release is BLOCKED due to critical regressions or failures. "
                "Engineering must correct rule logic before requesting approval."
            )
        elif human_review_triggers or warnings:
            status = "NEEDS_HUMAN_REVIEW"
            recommendation = (
                "Underwriting & Release Committee human review is required before proceeding. "
                "Review coverage gaps and risk triggers."
            )
        else:
            status = "READY_FOR_REVIEW"
            recommendation = (
                "Change has passed all deterministic regression tests with 100% verified evidence paths. "
                "Ready for formal Human Review Gate."
            )

        evidence_completeness_pct = 100.0 if not missing_tags and not blockers else max(100.0 - (len(blockers) * 35 + len(warnings) * 15), 10.0)

        return {
            "status": status,
            "is_blocked": len(blockers) > 0,
            "blockers": blockers,
            "warnings": warnings,
            "human_review_triggers": human_review_triggers,
            "evidence_completeness_pct": round(evidence_completeness_pct, 1),
            "recommendation": recommendation,
            "requires_human_approval": True,
            "governance_note": "READY_FOR_REVIEW does NOT authorize automatic production deployment.",
        }
