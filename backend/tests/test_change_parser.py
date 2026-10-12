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
