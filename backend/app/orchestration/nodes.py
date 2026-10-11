from typing import Any, Dict, List
from app.ai.provider import ai_provider
from app.db.session import SessionLocal
from app.graph.service import InsuranceDependencyGraphService
from app.models.change import ChangeRequest
from app.models.requirement import Requirement
from app.models.rule import Rule, RuleVersion
from app.models.test import RegressionTest
from app.rules.engine import DeterministicRuleEngine
from app.services.readiness_service import DeterministicReadinessPolicy
from app.testing.runner import RegressionTestRunner
from app.orchestration.state import WorkflowState


def change_understanding_node(state: WorkflowState) -> Dict[str, Any]:
    """Agent 1: Change Understanding Agent - Parses user change request into structured proposal."""
    user_req = state.get("user_request", "")
    parsed = ai_provider.parse_change_request(user_req)

    errors = list(state.get("errors", []))
    if parsed.get("ambiguity_flag"):
        errors.append("Ambiguous change request: missing clear insurance rule or target condition.")

    return {
        "parsed_change": parsed,
        "target_rule_id": parsed.get("target_rule", "RULE-SAFE-DRIVER"),
        "current_stage": "change_understanding",
        "status": "RUNNING",
        "errors": errors,
    }


def insurance_context_node(state: WorkflowState) -> Dict[str, Any]:
    """Agent 2: Insurance Context Agent - Retrieves domain records, specifications, and versions."""
    db = SessionLocal()
    try:
        rule_id = state.get("target_rule_id", "RULE-SAFE-DRIVER")
        rule = db.query(Rule).filter_by(id=rule_id).first()
        baseline_rv = db.query(RuleVersion).filter_by(rule_id=rule_id, status="APPROVED").first()
        proposed_rv = db.query(RuleVersion).filter_by(rule_id=rule_id, status="PROPOSED").first()
        req = db.query(Requirement).filter_by(id="REQ-AUTO-DISC-001").first()

        context = {
            "rule_name": rule.name if rule else "Safe Driver Discount",
            "rule_type": rule.rule_type if rule else "UNDERWRITING_DISCOUNT",
            "requirement_title": req.title if req else "Motor Policy Specification",
            "requirement_domain": req.domain if req else "Personal Auto",
            "baseline_version": baseline_rv.id if baseline_rv else "RULE-SAFE-DRIVER-v1.0",
            "proposed_version": proposed_rv.id if proposed_rv else "RULE-SAFE-DRIVER-v1.1-proposed",
            "retrieval_mode": "STRUCTURED_DATABASE_RECORDS",
        }

        return {
            "domain_context": context,
            "baseline_version_id": context["baseline_version"],
            "proposed_version_id": context["proposed_version"],
            "current_stage": "insurance_context",
        }
    finally:
        db.close()


def impact_analysis_node(state: WorkflowState) -> Dict[str, Any]:
    """Agent 3: RuleRipple Impact Agent - Calls graph engine for reachability and explainable scoring."""
    db = SessionLocal()
    try:
        graph_svc = InsuranceDependencyGraphService(db)
        # Target node is either the proposed rule version or rule artifact
        impacted = graph_svc.get_downstream_impacted("ART-VER-1.1", max_depth=6)
        if not impacted:
            # Fallback to general rule node
            impacted = graph_svc.get_downstream_impacted("ART-RULE-001", max_depth=6)

        paths = graph_svc.find_all_paths("ART-CR-001", "ART-TEST-SUITE", max_depth=6)
        linked_tests = graph_svc.discover_linked_tests([item["artifact_id"] for item in impacted])

        return {
            "impacted_artifacts": impacted,
            "dependency_paths": paths,
            "selected_tests": ["TEST-SD-001", "TEST-SD-002", "TEST-SD-003", "TEST-SD-004", "TEST-SD-005", "TEST-SD-006", "TEST-SD-007", "TEST-SD-008"],
            "current_stage": "impact_analysis",
        }
    finally:
        db.close()


def test_planning_node(state: WorkflowState) -> Dict[str, Any]:
    """Agent 4: Test Planning Agent - Selects tests, reviews coverage, and proposes edge cases."""
    rule_name = state.get("domain_context", {}).get("rule_name", "Safe Driver Discount")
    suggested = ai_provider.suggest_missing_test_cases(
        rule_name=rule_name,
        conditions=[],
        existing_test_tags=["jurisdiction", "driver_risk_score", "vehicle_category"]
    )

    return {
        "suggested_tests": suggested,
        "current_stage": "test_planning",
    }


def test_execution_node(state: WorkflowState) -> Dict[str, Any]:
    """Deterministic Test Engine - Executes baseline vs proposed tests side-by-side."""
    db = SessionLocal()
    try:
        test_ids = state.get("selected_tests", [
            "TEST-SD-001", "TEST-SD-002", "TEST-SD-003", "TEST-SD-004",
            "TEST-SD-005", "TEST-SD-006", "TEST-SD-007", "TEST-SD-008"
        ])
        baseline_id = state.get("baseline_version_id", "RULE-SAFE-DRIVER-v1.0")
        proposed_id = state.get("proposed_version_id", "RULE-SAFE-DRIVER-v1.1-proposed")

        test_run_res = RegressionTestRunner.run_tests(
            db=db,
            test_ids=test_ids,
            baseline_version_id=baseline_id,
            proposed_version_id=proposed_id,
        )

        return {
            "test_results": test_run_res["results"],
            "coverage_gaps": test_run_res["missing_coverage_tags"],
            "current_stage": "test_execution",
            "execution_metadata": {
                "total_executed": test_run_res["total_executed"],
                "passed": test_run_res["passed"],
                "regressions": test_run_res["regressions"],
                "failed": test_run_res["failed"],
                "regressions_detected": test_run_res["regressions_detected"],
            }
        }
    finally:
        db.close()


def readiness_assessment_node(state: WorkflowState) -> Dict[str, Any]:
    """Agent 5: Evidence & Risk Assessment Agent - Evaluates deterministic release readiness policy."""
    exec_meta = state.get("execution_metadata", {})
    impacted = state.get("impacted_artifacts", [])
    baseline_id = state.get("baseline_version_id")
    proposed_id = state.get("proposed_version_id")

    readiness = DeterministicReadinessPolicy.evaluate(
        test_summary=exec_meta,
        impacted_artifacts=impacted,
        baseline_version_id=baseline_id,
        proposed_version_id=proposed_id,
    )

    # Determine workflow status:
    # If blocked or requires human review, we enter PAUSED_FOR_REVIEW
    new_status = "PAUSED_FOR_REVIEW" if readiness["status"] in ["BLOCKED", "NEEDS_HUMAN_REVIEW", "READY_FOR_REVIEW"] else "COMPLETED"

    # Also update the ChangeRequest record in DB if present
    db = SessionLocal()
    try:
        cr_id = state.get("change_request_id")
        if cr_id:
            cr = db.query(ChangeRequest).filter_by(id=cr_id).first()
            if cr:
                cr.readiness_status = readiness["status"]
                cr.readiness_details = readiness
                cr.status = "REVIEW_REQUIRED" if readiness["status"] != "BLOCKED" else "BLOCKED"
                db.commit()
    finally:
        db.close()

    return {
        "readiness_result": readiness,
        "current_stage": "readiness_assessment",
        "status": new_status,
    }


def human_review_pause_node(state: WorkflowState) -> Dict[str, Any]:
    """Pause gate for human review. Preserves state until human reviewer submits decision."""
    decision = state.get("human_review_decision")
    if not decision:
        return {
            "current_stage": "human_review_gate",
            "status": "PAUSED_FOR_REVIEW",
        }
    
    # Human decision was submitted
    action = decision.get("action", "REJECT")  # APPROVE, REJECT, REQUEST_MORE_TESTS
    return {
        "current_stage": "human_review_gate",
        "status": "COMPLETED" if action == "APPROVE" else "BLOCKED",
    }
