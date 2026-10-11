import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_dashboard_summary_endpoint():
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_change_requests" in data
    assert "open_findings" in data


def test_rules_and_versions_endpoints():
    res = client.get("/api/rules")
    assert res.status_code == 200
    rules = res.json()
    assert len(rules) >= 1
    assert any(r["id"] == "RULE-SAFE-DRIVER" for r in rules)

    res_ver = client.get("/api/rules/RULE-SAFE-DRIVER/versions")
    assert res_ver.status_code == 200
    versions = res_ver.json()
    assert len(versions) >= 2


def test_dependency_graph_endpoint():
    res = client.get("/api/graph")
    assert res.status_code == 200
    data = res.json()
    assert len(data["nodes"]) >= 10
    assert len(data["edges"]) >= 10


def test_intentguard_simulation_endpoint():
    payload = {
        "transaction_id": "TXN-API-SIM-01",
        "jurisdiction": "NV",
        "driver_risk_score": 15,
        "vehicle_category": "SEDAN",
        "policy_active": True,
        "approved_reference_version_id": "RULE-SAFE-DRIVER-v1.0",
        "simulated_deployed_version_id": "RULE-SAFE-DRIVER-v1.1-proposed",
        "linked_change_id": "CR-2026-001"
    }
    res = client.post("/api/verification/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "DEVIATION"
    assert data["is_deviation"] is True
    assert data["finding_id"] is not None
