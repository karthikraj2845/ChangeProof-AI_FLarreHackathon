from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.rules.schema import (
    RuleDefinitionSchema,
    RuleCondition,
    ConditionOperator,
    ConditionEvaluationResult,
    RuleEvaluationResult,
)


class DeterministicRuleEngine:
    """
    Production-grade deterministic insurance rule evaluator.
    Evaluates versioned rule definitions against transaction payloads without LLM dependency.
    """

    @classmethod
    def evaluate_condition(cls, condition: RuleCondition, data: Dict[str, Any]) -> ConditionEvaluationResult:
        field = condition.field
        op = condition.operator
        expected = condition.value

        if field not in data or data[field] is None:
            # Field is absent or null
            if op == ConditionOperator.IS_NULL:
                return ConditionEvaluationResult(
                    field=field,
                    operator=op.value,
                    expected_value=expected,
                    actual_value=None,
                    passed=True,
                    reason=f"Field '{field}' is null/absent as expected."
                )
            return ConditionEvaluationResult(
                field=field,
                operator=op.value,
                expected_value=expected,
                actual_value=None,
                passed=False,
                reason=f"Missing required field '{field}' in transaction data."
            )

        actual = data[field]

        try:
            if op == ConditionOperator.EQ:
                passed = (actual == expected)
            elif op == ConditionOperator.NEQ:
                passed = (actual != expected)
            elif op == ConditionOperator.IN:
                passed = actual in (expected if isinstance(expected, (list, tuple, set)) else [expected])
            elif op == ConditionOperator.NOT_IN:
                passed = actual not in (expected if isinstance(expected, (list, tuple, set)) else [expected])
            elif op == ConditionOperator.GT:
                passed = float(actual) > float(expected)
            elif op == ConditionOperator.GTE:
                passed = float(actual) >= float(expected)
            elif op == ConditionOperator.LT:
                passed = float(actual) < float(expected)
            elif op == ConditionOperator.LTE:
                passed = float(actual) <= float(expected)
            elif op == ConditionOperator.NOT_NULL:
                passed = actual is not None
            elif op == ConditionOperator.IS_NULL:
                passed = actual is None
            else:
                passed = False
        except (ValueError, TypeError) as e:
            return ConditionEvaluationResult(
                field=field,
                operator=op.value,
                expected_value=expected,
                actual_value=actual,
                passed=False,
                reason=f"Type comparison error on '{field}': {str(e)}"
            )

        reason = (
            f"Condition met: {field} ({actual}) {op.value} {expected}"
            if passed
            else f"Condition failed: {field} ({actual}) does not satisfy {op.value} {expected}"
        )

        return ConditionEvaluationResult(
            field=field,
            operator=op.value,
            expected_value=expected,
            actual_value=actual,
            passed=passed,
            reason=reason
        )

    @classmethod
    def evaluate(
        cls,
        rule_def: Dict[str, Any] | RuleDefinitionSchema,
        input_data: Dict[str, Any],
        version_id: Optional[str] = None
    ) -> RuleEvaluationResult:
        if isinstance(rule_def, dict):
            rule_schema = RuleDefinitionSchema.model_validate(rule_def)
        else:
            rule_schema = rule_def

        vid = version_id or f"{rule_schema.rule_id}-{rule_schema.version}"

        # 1. Validate required inputs
        missing_fields: List[str] = []
        for req_field in rule_schema.required_inputs:
            if req_field not in input_data or input_data[req_field] is None:
                missing_fields.append(req_field)

        # 2. Evaluate all conditions
        condition_results: List[ConditionEvaluationResult] = []
        all_passed = True

        for condition in rule_schema.conditions:
            res = cls.evaluate_condition(condition, input_data)
            condition_results.append(res)
            if not res.passed:
                all_passed = False

        # If any required inputs are missing, overall evaluation fails
        if missing_fields:
            all_passed = False

        # 3. Determine outcome
        if all_passed:
            action = rule_schema.success_action
            explanation = (
                f"All {len(condition_results)} conditions passed for {vid}. "
                f"Awarded {action.discount_percentage}% discount ({action.discount_code})."
            )
        else:
            action = rule_schema.fallback_action
            failed_conditions = [c.reason for c in condition_results if not c.passed]
            if missing_fields:
                failed_conditions.append(f"Missing required input fields: {', '.join(missing_fields)}")
            explanation = (
                f"Rule evaluation failed for {vid}. "
                f"Reasons: {'; '.join(failed_conditions)}. "
                f"Outcome: {action.discount_percentage}% discount."
            )

        return RuleEvaluationResult(
            rule_id=rule_schema.rule_id,
            version_id=vid,
            eligible=action.eligible,
            discount_percentage=action.discount_percentage,
            discount_code=action.discount_code,
            passed_all_conditions=all_passed,
            condition_results=condition_results,
            missing_fields=missing_fields,
            explanation=explanation,
            execution_timestamp=datetime.now(timezone.utc)
        )
