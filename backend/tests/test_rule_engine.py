import pytest
from app.rules.engine import DeterministicRuleEngine
from app.rules.schema import RuleCondition, ConditionOperator


def test_rule_condition_operators():
    # Test numeric comparison
    cond_gt = RuleCondition(field="driver_risk_score", operator=ConditionOperator.LTE, value=25)
    assert DeterministicRuleEngine.evaluate_condition(cond_gt, {"driver_risk_score": 20}).passed is True
    assert DeterministicRuleEngine.evaluate_condition(cond_gt, {"driver_risk_score": 25}).passed is True
    assert DeterministicRuleEngine.evaluate_condition(cond_gt, {"driver_risk_score": 26}).passed is False

    # Test list inclusion
    cond_in = RuleCondition(field="jurisdiction", operator=ConditionOperator.IN, value=["CA", "TX", "FL"])
    assert DeterministicRuleEngine.evaluate_condition(cond_in, {"jurisdiction": "CA"}).passed is True
    assert DeterministicRuleEngine.evaluate_condition(cond_in, {"jurisdiction": "NV"}).passed is False

    # Test missing field
    assert DeterministicRuleEngine.evaluate_condition(cond_in, {}).passed is False


def test_rule_evaluation_baseline_success():
    rule_def = {
        "rule_id": "RULE-SAFE-DRIVER",
        "version": "1.0",
        "name": "Safe Driver Discount",
        "description": "Baseline rule",
        "required_inputs": ["jurisdiction", "driver_risk_score", "vehicle_category", "policy_active"],
        "conditions": [
            {"field": "jurisdiction", "operator": "in", "value": ["CA", "TX", "FL", "NY", "IL"]},
            {"field": "driver_risk_score", "operator": "lte", "value": 25},
            {"field": "vehicle_category", "operator": "in", "value": ["SEDAN", "SUV"]},
            {"field": "policy_active", "operator": "eq", "value": True},
        ],
        "success_action": {"eligible": True, "discount_percentage": 10.0, "discount_code": "SD_10"},
        "fallback_action": {"eligible": False, "discount_percentage": 0.0, "discount_code": None},
    }

    input_data = {
        "jurisdiction": "CA",
        "driver_risk_score": 18,
        "vehicle_category": "SEDAN",
        "policy_active": True,
    }
    result = DeterministicRuleEngine.evaluate(rule_def, input_data)
    assert result.eligible is True
    assert result.discount_percentage == 10.0
    assert result.passed_all_conditions is True


def test_rule_evaluation_baseline_rejection_unsupported_state():
    rule_def = {
        "rule_id": "RULE-SAFE-DRIVER",
        "version": "1.0",
        "name": "Safe Driver Discount",
        "description": "Baseline rule",
        "required_inputs": ["jurisdiction", "driver_risk_score", "vehicle_category", "policy_active"],
        "conditions": [
            {"field": "jurisdiction", "operator": "in", "value": ["CA", "TX", "FL", "NY", "IL"]},
            {"field": "driver_risk_score", "operator": "lte", "value": 25},
            {"field": "vehicle_category", "operator": "in", "value": ["SEDAN", "SUV"]},
            {"field": "policy_active", "operator": "eq", "value": True},
        ],
        "success_action": {"eligible": True, "discount_percentage": 10.0, "discount_code": "SD_10"},
        "fallback_action": {"eligible": False, "discount_percentage": 0.0, "discount_code": None},
    }

    # NV is not an eligible state
    input_data = {
        "jurisdiction": "NV",
        "driver_risk_score": 18,
        "vehicle_category": "SEDAN",
        "policy_active": True,
    }
    result = DeterministicRuleEngine.evaluate(rule_def, input_data)
    assert result.eligible is False
    assert result.discount_percentage == 0.0
    assert result.passed_all_conditions is False
