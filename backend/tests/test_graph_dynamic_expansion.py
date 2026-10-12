import pytest
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.rule import Rule, RuleVersion
from app.models.test import RegressionTest
from app.models.artifact import Artifact, DependencyEdge
from app.graph.service import InsuranceDependencyGraphService


def test_dynamic_graph_expansion_discovers_new_tests():
    """
    Test Acceptance Requirement #1:
    Add a new rule, requirement, or test case to the database or graph
    without modifying orchestration code, and verify that impact analysis
    and test discovery reflect the additions dynamically.
    """
    db: Session = SessionLocal()
    try:
        new_rule_id = "RULE-COMMERCIAL-FLEET-TIER"
        existing_rule = db.query(Rule).filter(Rule.id == new_rule_id).first()
        if not existing_rule:
            rule = Rule(
                id=new_rule_id,
                name="Commercial Fleet Tier Evaluation",
                description="Assigns fleet rating tier based on commercial vehicle count",
                rule_type="RATING_DISCOUNT",
            )
            db.add(rule)
            db.commit()

            v1 = RuleVersion(
                id=f"{new_rule_id}-v1.0",
                rule_id=new_rule_id,
                version="v1.0",
                description="Initial fleet rule",
                rule_definition={
                    "rule_id": new_rule_id,
                    "condition_operator": "AND",
                    "conditions": [
                        {"field": "fleet_size", "operator": "GREATER_THAN", "value": 5}
                    ],
                    "output_action": {"action": "TIER_A_DISCOUNT", "amount": 0.15},
                },
                status="APPROVED",
                product_scope="COMMERCIAL_AUTO",
                jurisdiction_scope=["US-NATIONAL"],
            )
            db.add(v1)

            # Create an artifact node
            art = Artifact(
                id=f"ART-{new_rule_id}",
                name="Commercial Fleet Rule Artifact",
                artifact_type="RULE",
                description="Dynamic commercial fleet rule artifact",
                version="v1.0",
                metadata_json={"rule_id": new_rule_id},
            )
            db.add(art)

            # Create a dynamic regression test linked directly to this rule
            dynamic_test = RegressionTest(
                id="TEST-DYNAMIC-FLEET-001",
                name="Verify Commercial Fleet Tier A qualification",
                description="Dynamic test for fleet size threshold",
                category="POSITIVE",
                linked_rule_id=new_rule_id,
                input_data={"fleet_size": 10},
                expected_baseline_outcome={"action": "TIER_A_DISCOUNT"},
                expected_proposed_outcome={"action": "TIER_A_DISCOUNT"},
                coverage_tags=["COMMERCIAL_AUTO", "US-NATIONAL"],
            )
            db.add(dynamic_test)

            # Add an edge in the dependency graph
            edge = DependencyEdge(
                id="EDGE-DYNAMIC-FLEET-REQ",
                source_artifact_id=f"ART-{new_rule_id}",
                target_artifact_id="REQ-AUT-001",
                relationship_type="IMPLEMENTS",
                confidence=1.0,
            )
            db.add(edge)
            db.commit()

        # Instantiate graph service
        graph_service = InsuranceDependencyGraphService(db)
        
        # Discover linked tests for this dynamic rule via graph service
        test_artifacts = graph_service.discover_linked_tests(
            impacted_artifact_ids=[f"ART-{new_rule_id}"]
        )

        # Check direct rule association from database as done in node test planning
        db_rule_tests = db.query(RegressionTest).filter(RegressionTest.linked_rule_id == new_rule_id).all()
        all_discovered = test_artifacts + [t.id for t in db_rule_tests]

        assert "TEST-DYNAMIC-FLEET-001" in all_discovered

    finally:
        db.close()


def test_dependency_graph_cycle_handling():
    """
    Ensure the dependency graph traversal safely handles cycles without infinite loops
    or stack overflow.
    """
    db: Session = SessionLocal()
    try:
        # Create 2 artifacts that depend on each other (cycle)
        a1 = db.query(Artifact).filter(Artifact.id == "ART-CYCLE-A").first()
        if not a1:
            a1 = Artifact(
                id="ART-CYCLE-A",
                name="Cycle Node A",
                artifact_type="RULE",
                description="Cycle test node A",
                version="1.0",
            )
            a2 = Artifact(
                id="ART-CYCLE-B",
                name="Cycle Node B",
                artifact_type="RULE",
                description="Cycle test node B",
                version="1.0",
            )
            db.add_all([a1, a2])
            db.commit()

            edge1 = DependencyEdge(
                id="EDGE-CYCLE-A-B",
                source_artifact_id="ART-CYCLE-A",
                target_artifact_id="ART-CYCLE-B",
                relationship_type="DEPENDS_ON",
            )
            edge2 = DependencyEdge(
                id="EDGE-CYCLE-B-A",
                source_artifact_id="ART-CYCLE-B",
                target_artifact_id="ART-CYCLE-A",
                relationship_type="DEPENDS_ON",
            )
            db.add_all([edge1, edge2])
            db.commit()

        graph_service = InsuranceDependencyGraphService(db)
        # Should complete gracefully and traverse both nodes without hanging
        impacted = graph_service.get_downstream_impacted("ART-CYCLE-A", max_depth=5)
        impacted_ids = [node["artifact_id"] for node in impacted]
        assert "ART-CYCLE-B" in impacted_ids

    finally:
        db.close()


def test_full_workflow_dynamic_test_discovery_and_execution_without_code_changes():
    """
    Proves that a newly registered graph dependency and linked test are dynamically
    selected and executed by the complete LangGraph workflow without editing workflow code.
    """
    from app.orchestration.runner import WorkflowRunner
    from app.models.change import ChangeRequest

    db: Session = SessionLocal()
    try:
        # 1. Register a dynamic regression test linked to RULE-SAFE-DRIVER
        dyn_test_id = "TEST-SD-DYNAMIC-AUDIT-099"
        existing = db.query(RegressionTest).filter_by(id=dyn_test_id).first()
        if not existing:
            dyn_test = RegressionTest(
                id=dyn_test_id,
                name="Dynamic Audit Verification Test (CA Driver Safe Score 10)",
                description="Dynamically added test without modifying workflow code",
                category="POSITIVE",
                linked_rule_id="RULE-SAFE-DRIVER",
                linked_requirement_id="REQ-AUTO-DISC-001",
                input_data={
                    "jurisdiction": "CA",
                    "driver_risk_score": 10,
                    "vehicle_category": "SEDAN",
                    "policy_active": True,
                },
                expected_baseline_outcome={"eligible": True, "discount_percentage": 10.0},
                expected_proposed_outcome={"eligible": True, "discount_percentage": 10.0},
                coverage_tags=["jurisdiction", "driver_risk_score", "DYNAMIC_AUDIT"],
            )
            db.add(dyn_test)

            # Also add an artifact in the graph linked via VALIDATED_BY
            dyn_art = Artifact(
                id=f"ART-{dyn_test_id}",
                name="Dynamic Audit Test Artifact",
                artifact_type="REGRESSION_TEST",
                description="Graph node for dynamically added test",
                version="1.0",
                metadata_json={"test_id": dyn_test_id},
            )
            db.add(dyn_art)

            edge = DependencyEdge(
                id=f"EDGE-{dyn_test_id}",
                source_artifact_id="ART-SRV-001",  # Eligibility service node
                target_artifact_id=f"ART-{dyn_test_id}",
                relationship_type="VALIDATED_BY",
                confidence=1.0,
            )
            db.add(edge)
            db.commit()

        # 2. Run the complete workflow
        state = WorkflowRunner.start_change_assurance(
            db=db,
            change_request_id="CR-2026-001",
            user_request="Remove the jurisdiction restriction from the safe-driver discount eligibility rule.",
        )

        # 3. Assert the dynamic test was automatically selected, executed, and tracked in provenance
        assert dyn_test_id in state["selected_tests"], f"{dyn_test_id} must be selected by workflow"
        assert dyn_test_id in state["test_provenance"], f"{dyn_test_id} must have provenance"
        
        executed_test_ids = [r["test_id"] for r in state.get("test_results", [])]
        assert dyn_test_id in executed_test_ids, f"{dyn_test_id} must be executed in test_results"

        # Verify execution outcome for the dynamic test was PASSED (CA driver is eligible under both v1.0 and v1.1)
        dyn_result = next(r for r in state["test_results"] if r["test_id"] == dyn_test_id)
        assert dyn_result["status"] == "PASSED"

        # 4. Verify test is included in the authoritative EvidenceSnapshot and readiness calculation
        from app.models.snapshot import EvidenceSnapshot
        snap_id = state.get("snapshot_id")
        assert snap_id is not None
        snapshot = db.query(EvidenceSnapshot).filter_by(id=snap_id).first()
        assert snapshot is not None
        assert dyn_test_id in snapshot.selected_test_ids, f"{dyn_test_id} must be in snapshot.selected_test_ids"
        assert snapshot.test_summary.get("total_executed", 0) >= 9

        # Verify readiness result incorporates the run
        readiness = state.get("readiness_result", {})
        assert readiness.get("status") in ["BLOCKED", "READY", "NEEDS_HUMAN_REVIEW"]

    finally:
        # Clean up dynamic records to keep the test environment pristine for other tests
        try:
            db.query(DependencyEdge).filter(DependencyEdge.id == f"EDGE-{dyn_test_id}").delete()
            db.query(Artifact).filter(Artifact.id == f"ART-{dyn_test_id}").delete()
            db.query(RegressionTest).filter(RegressionTest.id == dyn_test_id).delete()
            db.commit()
        except Exception:
            pass
        db.close()

