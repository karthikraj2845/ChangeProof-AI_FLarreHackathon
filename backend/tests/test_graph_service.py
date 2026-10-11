import pytest
from app.db.session import SessionLocal
from app.graph.service import InsuranceDependencyGraphService


def test_graph_loading_and_traversal():
    db = SessionLocal()
    try:
        service = InsuranceDependencyGraphService(db)
        assert len(service.graph.nodes) >= 10
        assert len(service.graph.edges) >= 10

        # Downstream traversal from proposed version
        impacted = service.get_downstream_impacted("ART-VER-1.1", max_depth=5)
        assert len(impacted) > 0

        impacted_ids = [item["artifact_id"] for item in impacted]
        assert "ART-RULE-001" in impacted_ids
        assert "ART-REQ-001" in impacted_ids

        # Discover linked tests
        linked_tests = service.discover_linked_tests(impacted_ids)
        assert "ART-TEST-SUITE" in linked_tests
    finally:
        db.close()


def test_impact_score_calculation():
    db = SessionLocal()
    try:
        service = InsuranceDependencyGraphService(db)
        score_data = service.calculate_impact_score("ART-SVC-RATING")
        assert 0.0 <= score_data["total_score"] <= 100.0
        assert "reach_factor" in score_data
        assert "criticality_factor" in score_data
        assert "proximity_factor" in score_data
        assert "uncertainty_factor" in score_data
    finally:
        db.close()
