import pytest
from app.ai.provider import ai_provider, ParsedChangeSchema


def test_valid_safe_driver_discount_change():
    req = "Remove the jurisdiction restriction from the safe-driver discount eligibility rule."
    res = ai_provider.parse_change_request(req)
    assert res["target_rule"] == "RULE-SAFE-DRIVER"
    assert res["operation"] == "REMOVE_CONDITION"
    assert res["condition_field"] == "jurisdiction"
    assert res["ambiguity_flag"] is False
    assert res["confidence"] >= 0.90


def test_modify_driver_risk_score_threshold():
    req = "Increase driver risk score threshold to 30 for telematics discount"
    res = ai_provider.parse_change_request(req)
    assert res["target_rule"] == "RULE-SAFE-DRIVER"
    assert res["operation"] == "MODIFY_THRESHOLD"
    assert res["condition_field"] == "driver_risk_score"
    assert res["ambiguity_flag"] is False


def test_empty_request_handling():
    res = ai_provider.parse_change_request("")
    assert res["ambiguity_flag"] is True
    assert res["operation"] == "AMBIGUOUS_REQUEST"
    assert res["confidence"] == 0.0


def test_vague_request_handling():
    res = ai_provider.parse_change_request("change please")
    assert res["ambiguity_flag"] is True
    assert res["operation"] == "AMBIGUOUS_REQUEST"
    assert res["confidence"] < 0.30


def test_unsupported_operation_handling():
    res = ai_provider.parse_change_request("Modify the blockchain hash for cryptocurrency billing")
    assert res["ambiguity_flag"] is True
    assert res["operation"] == "UNSUPPORTED_OPERATION"
    assert res["condition_field"] == "unknown"


def test_contradictory_request_handling():
    res = ai_provider.parse_change_request("Approve and deny safe driver discounts simultaneously")
    assert res["ambiguity_flag"] is True
    assert res["operation"] == "AMBIGUOUS_REQUEST"


def test_pydantic_schema_validation_untrusted_input():
    # Valid model validation
    valid_model = ParsedChangeSchema(
        target_rule="RULE-SAFE-DRIVER",
        operation="REMOVE_CONDITION",
        condition_field="jurisdiction",
        description="Valid parsed request",
        confidence=0.95,
    )
    assert valid_model.target_rule == "RULE-SAFE-DRIVER"
    assert valid_model.confidence == 0.95

    # Out-of-bounds confidence clamped
    clamped_model = ParsedChangeSchema(
        target_rule="RULE-TEST",
        operation="MODIFY_CONDITION",
        condition_field="vehicle_category",
        description="Confidence clamp test",
        confidence=1.5,
    )
    assert clamped_model.confidence == 1.0


def test_unknown_rule_does_not_default_to_safe_driver():
    """An unknown rule must not silently default to RULE-SAFE-DRIVER."""
    res = ai_provider.parse_change_request("Update the threshold for rule-cyber-security-posture to 95")
    assert res["target_rule"] == "RULE-CYBER-SECURITY-POSTURE"
    # Even if target_rule parsed from token, if unknown condition field, it's flagged as unsupported/ambiguous
    assert res["target_rule"] != "RULE-SAFE-DRIVER"


def test_ambiguous_target_flags_ambiguity_without_defaulting():
    """A generic request without rule identity must not silently choose RULE-SAFE-DRIVER."""
    res = ai_provider.parse_change_request("Remove the maximum limit on policy payouts")
    assert res["target_rule"] != "RULE-SAFE-DRIVER"
    assert res["ambiguity_flag"] is True


def test_insurance_context_node_fails_safely_on_unknown_rule():
    """Workflow node fails safely with FAILED status and error when target rule does not exist."""
    from app.orchestration.nodes import insurance_context_node
    state = {
        "workflow_id": "WF-UNKNOWN-TEST",
        "target_rule_id": "RULE-NON-EXISTENT-XYZ",
        "user_request": "Test request",
    }
    result = insurance_context_node(state)
    assert result.get("status") == "FAILED"
    assert any("not found in registry" in err for err in result.get("errors", []))


def test_impact_analysis_node_fails_safely_on_unresolved_rule():
    """Impact analysis node fails safely when target rule is missing/None."""
    from app.orchestration.nodes import impact_analysis_node
    state = {
        "workflow_id": "WF-MISSING-TARGET",
        "target_rule_id": None,
        "user_request": "Test request",
    }
    result = impact_analysis_node(state)
    assert "TARGET_RULE_UNRESOLVED" in result.get("coverage_gaps", [])
    assert result.get("impacted_artifacts") == []
    assert result.get("selected_tests") == []
