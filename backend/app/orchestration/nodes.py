from typing import Any, Dict, List, Optional
from app.ai.provider import ai_provider
from app.db.session import SessionLocal
from app.graph.service import InsuranceDependencyGraphService
from app.models.change import ChangeRequest
from app.models.requirement import Requirement
from app.models.rule import Rule, RuleVersion
from app.models.test import RegressionTest
from app.rules.engine import DeterministicRuleEngine
from app.services.readiness_service import DeterministicReadinessPolicy
from app.services.snapshot_service import SnapshotService
from app.testing.runner import RegressionTestRunner
from app.orchestration.state import WorkflowState


def change_understanding_node(state: WorkflowState) -> Dict[str, Any]:
    """Agent 1: Change Understanding Agent - Parses user change request into structured proposal."""
    user_req = state.get("user_request", "")
    parsed = ai_provider.parse_change_request(user_req)

    errors = list(state.get("errors", []))
    warnings = list(state.get("warnings", []))

    if parsed.get("ambiguity_flag"):
        errors.append("Ambiguous change request: missing clear insurance rule or target condition.")

    target_rule = parsed.get("target_rule") or state.get("target_rule_id", "RULE-SAFE-DRIVER")

    return {
        "parsed_change": parsed,
        "target_rule_id": target_rule,
        "current_stage": "change_understanding",
        "status": "RUNNING",
        "errors": errors,
        "warnings": warnings,
    }


def insurance_context_node(state: WorkflowState) -> Dict[str, Any]:
    """Agent 2: Insurance Context Agent - Dynamically retrieves domain records, specifications, and versions."""
    db = SessionLocal()
    try:
        rule_id = state.get("target_rule_id") or "RULE-SAFE-DRIVER"
        rule = db.query(Rule).filter_by(id=rule_id).first()

        # Resolve baseline and proposed versions dynamically
        baseline_id = state.get("baseline_version_id")
        proposed_id = state.get("proposed_version_id")

        baseline_rv = None
        if baseline_id:
            baseline_rv = db.query(RuleVersion).filter_by(id=baseline_id).first()
        if not baseline_rv:
            baseline_rv = db.query(RuleVersion).filter_by(rule_id=rule_id, status="APPROVED").order_by(RuleVersion.created_at.desc()).first()

        proposed_rv = None
        if proposed_id:
            proposed_rv = db.query(RuleVersion).filter_by(id=proposed_id).first()
        if not proposed_rv:
            proposed_rv = db.query(RuleVersion).filter_by(rule_id=rule_id, status="PROPOSED").order_by(RuleVersion.created_at.desc()).first()

        # Find linked requirement dynamically
        req = db.query(Requirement).first()

        resolved_baseline = baseline_rv.id if baseline_rv else "RULE-SAFE-DRIVER-v1.0"
        resolved_proposed = proposed_rv.id if proposed_rv else "RULE-SAFE-DRIVER-v1.1-proposed"

        context = {
            "rule_id": rule.id if rule else rule_id,
            "rule_name": rule.name if rule else "Underwriting Rule",
            "rule_type": rule.rule_type if rule else "UNDERWRITING_DISCOUNT",
            "requirement_id": req.id if req else "REQ-AUTO-DISC-001",
            "requirement_title": req.title if req else "Policy Specification",
            "requirement_domain": req.domain if req else "Personal Auto",
            "baseline_version": resolved_baseline,
            "proposed_version": resolved_proposed,
            "retrieval_mode": "STRUCTURED_DATABASE_RECORDS",
        }

        return {
            "domain_context": context,
            "target_rule_id": rule_id,
            "baseline_version_id": resolved_baseline,
            "proposed_version_id": resolved_proposed,
            "current_stage": "insurance_context",
        }
    finally:
        db.close()


def impact_analysis_node(state: WorkflowState) -> Dict[str, Any]:
    """Agent 3: RuleRipple Impact Agent - Dynamically traverses graph for reachability and linked tests."""
    db = SessionLocal()
    try:
        graph_svc = InsuranceDependencyGraphService(db)
        proposed_v_id = state.get("proposed_version_id", "RULE-SAFE-DRIVER-v1.1-proposed")
        target_rule_id = state.get("target_rule_id", "RULE-SAFE-DRIVER")
        cr_id = state.get("change_request_id", "CR-2026-001")

        # Resolve starting artifact dynamically
        source_art = graph_svc.find_artifact_for_entity(proposed_v_id)
        if not source_art:
            source_art = graph_svc.find_artifact_for_entity(target_rule_id)
        if not source_art:
            source_art = "ART-VER-1.1" if "ART-VER-1.1" in graph_svc.graph else list(graph_svc.graph.nodes)[0]

        impacted = graph_svc.get_downstream_impacted(source_art, max_depth=6)

        # Find paths from CR to test suite
        cr_art = graph_svc.find_artifact_for_entity(cr_id) or "ART-CR-001"
        test_suites = [n for n, d in graph_svc.graph.nodes(data=True) if d.get("artifact_type") in ["REGRESSION_TEST", "TEST_SUITE"]]
        paths = []
        for ts in test_suites:
            found_paths = graph_svc.find_all_paths(cr_art, ts, max_depth=6)
            if found_paths:
                paths.extend(found_paths)

        # Dynamically discover regression tests connected to impacted artifacts
        impacted_ids = [item["artifact_id"] for item in impacted]
        discovered_test_artifacts = graph_svc.discover_linked_tests(impacted_ids)

        # Build provenance mapping for every test
        test_provenance: Dict[str, Dict[str, Any]] = {}

        # 1. Tests linked via graph test suites/artifacts
        for test_art_id in discovered_test_artifacts:
            # Check if this artifact directly represents a RegressionTest ID in DB
            db_test = db.query(RegressionTest).filter_by(id=test_art_id).first()
            if db_test:
                test_provenance[db_test.id] = {
                    "source": "GRAPH_DEPENDENCY",
                    "artifact_id": test_art_id,
                    "target_rule_id": target_rule_id,
                    "reason": f"Discovered directly via graph edge connected to {test_art_id}",
                }

        # 2. Tests linked directly to the target rule in the database
        db_rule_tests = db.query(RegressionTest).filter(RegressionTest.linked_rule_id == target_rule_id).all()
        for t in db_rule_tests:
            if t.id not in test_provenance:
                test_provenance[t.id] = {
                    "source": "RULE_DIRECT_LINK",
                    "target_rule_id": target_rule_id,
                    "reason": f"Authoritative test registered for rule {target_rule_id}",
                }

        # 3. Tests linked to requirements in the impacted blast radius
        impacted_req_ids = [
            item["artifact_id"] for item in impacted
            if item.get("artifact_type") == "REQUIREMENT" or item.get("name", "").startswith("REQ-")
        ]
        if impacted_req_ids:
            req_tests = db.query(RegressionTest).filter(RegressionTest.linked_requirement_id.in_(impacted_req_ids)).all()
            for t in req_tests:
                if t.id not in test_provenance:
                    test_provenance[t.id] = {
                        "source": "REQUIREMENT_TRACEABILITY",
                        "target_rule_id": target_rule_id,
                        "reason": f"Traceable to impacted requirement {t.linked_requirement_id}",
                    }

        # 4. Mandatory safety/invariant baseline tests for target rule (if present in DB)
        candidate_mandatory = ["TEST-SD-001", "TEST-SD-002", "TEST-SD-007"]
        mandatory_in_db = db.query(RegressionTest).filter(
            RegressionTest.id.in_(candidate_mandatory),
            RegressionTest.linked_rule_id == target_rule_id
        ).all()
        for m in mandatory_in_db:
            if m.id not in test_provenance:
                test_provenance[m.id] = {
                    "source": "MANDATORY_INVARIANT_SAFETY",
                    "target_rule_id": target_rule_id,
                    "reason": "Mandatory safety baseline/boundary invariant for rule",
                }

        final_selected_tests = sorted(list(test_provenance.keys()))

        # If no tests discovered at all, report coverage gap
        coverage_gaps = list(state.get("coverage_gaps", []))
        if not final_selected_tests:
            coverage_gaps.append(f"No regression tests mapped to rule '{target_rule_id}' or its impacted dependencies.")

        return {
            "impacted_artifacts": impacted,
            "dependency_paths": paths,
            "selected_tests": final_selected_tests,
            "test_provenance": test_provenance,
            "coverage_gaps": coverage_gaps,
            "current_stage": "impact_analysis",
        }
    finally:
        db.close()


def test_planning_node(state: WorkflowState) -> Dict[str, Any]:
    """Agent 4: Test Planning Agent - Proposes edge-case test cases using actual parsed rule conditions."""
    domain_ctx = state.get("domain_context", {})
    rule_name = domain_ctx.get("rule_name", "Safe Driver Discount")
    parsed_change = state.get("parsed_change", {})
    
    # Extract actual rule conditions from domain context or database
    db = SessionLocal()
    conditions = []
    try:
        proposed_v_id = state.get("proposed_version_id")
        if proposed_v_id:
            pv = db.query(RuleVersion).filter_by(id=proposed_v_id).first()
            if pv and isinstance(pv.rule_definition, dict):
                conditions = pv.rule_definition.get("conditions", [])
    finally:
        db.close()

    # Pass actual rule conditions and parsed fields to test planner
    affected_field = parsed_change.get("condition_field")
    existing_tags = ["jurisdiction", "driver_risk_score", "vehicle_category"]
    if affected_field and affected_field not in existing_tags:
        existing_tags.append(affected_field)

    suggested = ai_provider.suggest_missing_test_cases(
        rule_name=rule_name,
        conditions=conditions,
        existing_test_tags=existing_tags
    )

    return {
        "suggested_tests": suggested,
        "current_stage": "test_planning",
    }


def test_execution_node(state: WorkflowState) -> Dict[str, Any]:
    """Deterministic Test Engine - Executes baseline vs proposed tests side-by-side with persistence."""
    db = SessionLocal()
    try:
        test_ids = state.get("selected_tests", [])
        baseline_id = state.get("baseline_version_id", "RULE-SAFE-DRIVER-v1.0")
        proposed_id = state.get("proposed_version_id", "RULE-SAFE-DRIVER-v1.1-proposed")
        wf_id = state.get("workflow_id", "WF-TEST")

        # Run tests with verification run tracking
        test_run_res = RegressionTestRunner.run_tests(
            db=db,
            test_ids=test_ids,
            baseline_version_id=baseline_id,
            proposed_version_id=proposed_id,
            verification_run_id=wf_id,
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
                "missing_coverage_tags": test_run_res["missing_coverage_tags"],
            }
        }
    finally:
        db.close()


def readiness_assessment_node(state: WorkflowState) -> Dict[str, Any]:
    """Agent 5: Evidence & Risk Assessment Agent - Evaluates deterministic policy and creates immutable snapshot."""
    exec_meta = state.get("execution_metadata", {})
    impacted = state.get("impacted_artifacts", [])
    baseline_id = state.get("baseline_version_id")
    proposed_id = state.get("proposed_version_id")
    target_rule_id = state.get("target_rule_id", "RULE-SAFE-DRIVER")
    cr_id = state.get("change_request_id", "CR-2026-001")
    wf_id = state.get("workflow_id")
    selected_tests = state.get("selected_tests", [])

    # 1. Deterministic Readiness Evaluation
    readiness = DeterministicReadinessPolicy.evaluate(
        test_summary=exec_meta,
        impacted_artifacts=impacted,
        baseline_version_id=baseline_id,
        proposed_version_id=proposed_id,
    )

    # 2. Immutable Evidence Snapshot Creation
    db = SessionLocal()
    snapshot_id = None
    snapshot_hash = None
    try:
        test_provenance = state.get("test_provenance", {})
        snapshot = SnapshotService.create_snapshot(
            db=db,
            change_request_id=cr_id,
            workflow_run_id=wf_id,
            target_rule_id=target_rule_id,
            baseline_version_id=baseline_id or "UNKNOWN",
            proposed_version_id=proposed_id or "UNKNOWN",
            test_summary=exec_meta,
            impacted_artifacts=impacted,
            selected_test_ids=selected_tests,
            readiness_result=readiness,
            test_provenance=test_provenance,
        )
        snapshot_id = snapshot.id
        snapshot_hash = snapshot.snapshot_hash

        # Update ChangeRequest in DB
        cr = db.query(ChangeRequest).filter_by(id=cr_id).first()
        if cr:
            cr.readiness_status = readiness["status"]
            cr.readiness_details = readiness
            cr.status = "BLOCKED" if readiness["status"] == "BLOCKED" else "REVIEW_REQUIRED"
            db.commit()
    finally:
        db.close()

    # Determine status: NEEDS_HUMAN_REVIEW if blocked or requires review
    node_status = "BLOCKED" if readiness["status"] == "BLOCKED" else "NEEDS_HUMAN_REVIEW"

    return {
        "readiness_result": readiness,
        "snapshot_id": snapshot_id,
        "snapshot_hash": snapshot_hash,
        "current_stage": "readiness_assessment",
        "status": node_status,
    }


def human_review_pause_node(state: WorkflowState) -> Dict[str, Any]:
    """Human Review Gate: Evaluates submitted decision with cryptographic snapshot and regression blocker guards."""
    decision = state.get("human_review_decision")
    readiness = state.get("readiness_result", {})
    is_blocked = readiness.get("is_blocked", False) or readiness.get("status") == "BLOCKED"

    if not decision:
        return {
            "current_stage": "human_review_gate",
            "status": "BLOCKED" if is_blocked else "NEEDS_HUMAN_REVIEW",
        }

    action = decision.get("action", "REJECT").upper()

    # Enforce Governance Rule: Ordinary human approval CANNOT override a failed regression suite
    if action == "APPROVE" and is_blocked:
        errors = list(state.get("errors", []))
        errors.append("GOVERNANCE REJECTION: Approval denied because release is strictly BLOCKED by deterministic regression policy.")
        return {
            "current_stage": "human_review_gate",
            "status": "BLOCKED",
            "errors": errors,
        }

    if action == "APPROVE":
        final_status = "READY_FOR_REVIEW"
    elif action == "REVISION_REQUIRED" or action == "REQUEST_MORE_TESTS":
        final_status = "REVISION_REQUIRED"
    elif action == "REJECT":
        final_status = "REJECTED"
    else:
        final_status = "BLOCKED"

    return {
        "current_stage": "human_review_gate",
        "status": final_status,
    }
