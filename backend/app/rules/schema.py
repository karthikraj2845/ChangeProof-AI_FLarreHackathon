from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConditionOperator(str, Enum):
    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    NOT_IN = "not_in"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IS_NULL = "is_null"
    NOT_NULL = "not_null"


class RuleCondition(BaseModel):
    field: str
    operator: ConditionOperator
    value: Any = None
    description: Optional[str] = None
    mandatory: bool = True


class RuleAction(BaseModel):
    eligible: bool = False
    discount_percentage: float = 0.0
    discount_code: Optional[str] = None
    message: Optional[str] = None


class RuleDefinitionSchema(BaseModel):
    rule_id: str
    version: str
    name: str
    description: str
    required_inputs: List[str] = Field(default_factory=list)
    conditions: List[RuleCondition] = Field(default_factory=list)
    success_action: RuleAction
    fallback_action: RuleAction
    product_scope: str = "PERSONAL_AUTO"
    jurisdiction_scope: Optional[List[str]] = None


class ConditionEvaluationResult(BaseModel):
    field: str
    operator: str
    expected_value: Any
    actual_value: Any
    passed: bool
    reason: str


class RuleEvaluationResult(BaseModel):
    rule_id: str
    version_id: str
    eligible: bool
    discount_percentage: float
    discount_code: Optional[str] = None
    passed_all_conditions: bool
    condition_results: List[ConditionEvaluationResult]
    missing_fields: List[str]
    explanation: str
    execution_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
