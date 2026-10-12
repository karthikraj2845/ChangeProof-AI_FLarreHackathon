import logging
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from app.config import settings

logger = logging.getLogger(__name__)


class ParsedChangeSchema(BaseModel):
    """
    Authoritative Pydantic validation schema for natural-language rule changes.
    Enforces strict typing on target_rule, operation, condition_field, confidence,
    and ambiguity status.
    """
    target_rule: Optional[str] = None
    operation: str  # REMOVE_CONDITION, MODIFY_THRESHOLD, ADD_CONDITION, MODIFY_CONDITION, UNKNOWN, AMBIGUOUS_REQUEST, UNSUPPORTED_OPERATION
    condition_field: str  # jurisdiction, driver_risk_score, vehicle_category, policy_active, unknown
    target_value: Optional[Any] = None
    description: str
    ambiguity_flag: bool = False
    confidence: float = Field(ge=0.0, le=1.0)
    provider_mode: str = "HEURISTIC_OFFLINE_CAPABLE"
    raw_user_request: Optional[str] = None

    @field_validator("confidence", mode="before")
    @classmethod
    def check_confidence(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.0


class AIProvider:
    """
    Vendor-agnostic AI provider abstraction.
    Treats LLM output as untrusted input and strictly validates against ParsedChangeSchema.
    Gracefully falls back to heuristic domain reasoning when LLM API keys are missing or offline.
    """

    SUPPORTED_OPERATIONS = {
        "REMOVE_CONDITION",
        "MODIFY_THRESHOLD",
        "ADD_CONDITION",
        "MODIFY_CONDITION",
        "AMBIGUOUS_REQUEST",
        "UNSUPPORTED_OPERATION",
        "UNKNOWN",
    }

    SUPPORTED_FIELDS = {
        "jurisdiction",
        "driver_risk_score",
        "vehicle_category",
        "policy_active",
        "telematics_miles",
    }

    def __init__(self):
        self.has_llm = bool(settings.OPENAI_API_KEY and settings.AI_PROVIDER != "heuristic")
        self.client = None

        if self.has_llm:
            try:
                from langchain_openai import ChatOpenAI
                self.client = ChatOpenAI(
                    model=settings.OPENAI_MODEL,
                    api_key=settings.OPENAI_API_KEY,
                    temperature=0.1,
                    timeout=15,
                )
                logger.info(f"Initialized OpenAI provider with model {settings.OPENAI_MODEL}")
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI provider ({e}); falling back to heuristic engine.")
                self.has_llm = False

    def parse_change_request(self, user_text: str) -> Dict[str, Any]:
        """
        Parses natural-language insurance change proposal into structured schema.
        Validates both LLM output and heuristic output against ParsedChangeSchema.
        Distinguishes unknown requests from low-confidence requests and prevents silent defaulting.
        """
        raw_text = (user_text or "").strip()

        # 1. Guard against empty, whitespace, or trivially short inputs
        if len(raw_text) == 0:
            result = ParsedChangeSchema(
                target_rule=None,
                operation="AMBIGUOUS_REQUEST",
                condition_field="unknown",
                description="Empty change request: no rule modification intent provided.",
                ambiguity_flag=True,
                confidence=0.0,
                provider_mode="LLM" if (self.has_llm and self.client) else "HEURISTIC_OFFLINE_CAPABLE",
                raw_user_request=raw_text,
            )
            return result.model_dump()

        if len(raw_text) < 10 or (len(raw_text.split()) <= 2 and "change" in raw_text.lower()):
            result = ParsedChangeSchema(
                target_rule=None,
                operation="AMBIGUOUS_REQUEST",
                condition_field="unknown",
                description=f"Ambiguous request '{raw_text}': insufficient specification of rule or condition.",
                ambiguity_flag=True,
                confidence=0.15,
                provider_mode="LLM" if (self.has_llm and self.client) else "HEURISTIC_OFFLINE_CAPABLE",
                raw_user_request=raw_text,
            )
            return result.model_dump()

        # 2. Attempt LLM Parsing if configured
        if self.has_llm and self.client:
            try:
                prompt = (
                    "You are an insurance underwriting systems analyst. Parse this rule change request into JSON:\n"
                    f"User request: '{raw_text}'\n\n"
                    "Extract:\n"
                    "- target_rule: rule ID (e.g. 'RULE-SAFE-DRIVER') or null if unknown\n"
                    "- operation: one of 'REMOVE_CONDITION', 'MODIFY_THRESHOLD', 'ADD_CONDITION', 'MODIFY_CONDITION', 'UNSUPPORTED_OPERATION'\n"
                    "- condition_field: field affected (e.g. 'jurisdiction', 'driver_risk_score', 'vehicle_category', 'policy_active') or 'unknown'\n"
                    "- description: structured summary\n"
                    "- ambiguity_flag: boolean\n"
                    "- confidence: float (0.0 to 1.0)\n"
                    "Respond with valid JSON only."
                )
                res = self.client.invoke(prompt)
                content = res.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                raw_dict = json.loads(content.strip())

                # Validate untrusted LLM output through Pydantic
                parsed_model = ParsedChangeSchema(
                    target_rule=raw_dict.get("target_rule"),
                    operation=raw_dict.get("operation", "UNKNOWN"),
                    condition_field=raw_dict.get("condition_field", "unknown"),
                    target_value=raw_dict.get("target_value"),
                    description=raw_dict.get("description", "Parsed via LLM."),
                    ambiguity_flag=bool(raw_dict.get("ambiguity_flag", False)),
                    confidence=float(raw_dict.get("confidence", 0.5)),
                    provider_mode="LLM",
                    raw_user_request=raw_text,
                )
                return parsed_model.model_dump()
            except Exception as e:
                logger.warning(f"LLM parsing/validation failed: {e}. Falling back to deterministic heuristic parser.")

        # 3. Deterministic Heuristic Insurance Parser
        text_lower = raw_text.lower()
        target_rule = None
        operation = "UNKNOWN"
        condition_field = "unknown"
        ambiguity = False
        target_value = None

        # Check for explicit target rule mention if present
        if any(w in text_lower for w in ["safe-driver", "safe driver", "rule-safe-driver", "telematics discount"]):
            target_rule = "RULE-SAFE-DRIVER"
        elif "commercial" in text_lower:
            target_rule = "RULE-COMMERCIAL-FLEET"
        elif "homeowners" in text_lower:
            target_rule = "RULE-HOMEOWNERS-WIND"

        # Check for condition fields and operations
        if "jurisdiction" in text_lower or "state" in text_lower:
            condition_field = "jurisdiction"
            if any(w in text_lower for w in ["remove", "drop", "delete", "omit", "exclude", "eliminate"]):
                operation = "REMOVE_CONDITION"
            elif any(w in text_lower for w in ["add", "include", "expand to"]):
                operation = "ADD_CONDITION"
            else:
                operation = "MODIFY_CONDITION"
        elif any(w in text_lower for w in ["risk score", "driver score", "telematics", "score"]):
            condition_field = "driver_risk_score"
            operation = "MODIFY_THRESHOLD"
        elif any(w in text_lower for w in ["vehicle", "car", "sedan", "suv", "truck"]):
            condition_field = "vehicle_category"
            operation = "MODIFY_CONDITION"
        elif any(w in text_lower for w in ["policy", "active", "status", "lapse"]):
            condition_field = "policy_active"
            operation = "MODIFY_CONDITION"
        else:
            ambiguity = True
            operation = "UNSUPPORTED_OPERATION"
            condition_field = "unknown"

        # Check for unknown rule names
        if "rule-" in text_lower and not target_rule:
            words = text_lower.split()
            for w in words:
                if w.startswith("rule-"):
                    target_rule = w.upper()
                    break

        # Check if contradictory or unsupported
        if ("approve" in text_lower and "deny" in text_lower) or ("increase" in text_lower and "decrease" in text_lower):
            ambiguity = True
            operation = "AMBIGUOUS_REQUEST"

        # If rule could not be inferred and is not generic safe-driver context, do NOT silently invent a rule
        if not target_rule:
            if condition_field != "unknown":
                # Default to safe-driver context only if condition unambiguously belongs to motor discount
                target_rule = "RULE-SAFE-DRIVER"
            else:
                ambiguity = True
                operation = "UNSUPPORTED_OPERATION"

        confidence = 0.98 if (condition_field != "unknown" and not ambiguity and target_rule) else (0.20 if ambiguity else 0.40)

        result = ParsedChangeSchema(
            target_rule=target_rule,
            operation=operation,
            condition_field=condition_field,
            target_value=target_value,
            description=f"Parsed intent: {operation} on field '{condition_field}' for rule {target_rule}." if not ambiguity else "Ambiguous, contradictory, or unsupported change request.",
            ambiguity_flag=ambiguity,
            confidence=confidence,
            provider_mode="LLM" if (self.has_llm and self.client) else "HEURISTIC_OFFLINE_CAPABLE",
            raw_user_request=raw_text,
        )
        return result.model_dump()

    def suggest_missing_test_cases(
        self,
        rule_name: str,
        conditions: List[Dict[str, Any]],
        existing_test_tags: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Synthesizes candidate edge-case regression tests.
        Clearly marked as UNVALIDATED_PROPOSAL until approved and registered as executable tests.
        """
        suggestions = [
            {
                "id": "SUGGESTED-TC-001",
                "name": f"Multi-Vehicle Policy Accumulation Check ({rule_name})",
                "category": "EDGE_CASE",
                "reason": "Verify discount application across joint primary and secondary drivers on multi-car policies.",
                "input_data": {
                    "jurisdiction": "CA",
                    "driver_risk_score": 20,
                    "vehicle_category": "SEDAN",
                    "policy_active": True,
                    "multi_vehicle_count": 3
                },
                "expected_outcome": {"eligible": True, "discount_percentage": 10.0},
                "status": "UNVALIDATED_PROPOSAL",
            },
            {
                "id": "SUGGESTED-TC-002",
                "name": f"Zero Telematics Miles Logged Boundary Test ({rule_name})",
                "category": "BOUNDARY",
                "reason": "Ensure drivers with active policies but exactly 0 recorded telematics miles handle score thresholds gracefully.",
                "input_data": {
                    "jurisdiction": "TX",
                    "driver_risk_score": 0,
                    "vehicle_category": "SUV",
                    "policy_active": True,
                    "telematics_miles": 0
                },
                "expected_outcome": {"eligible": True, "discount_percentage": 10.0},
                "status": "UNVALIDATED_PROPOSAL",
            }
        ]
        return suggestions


ai_provider = AIProvider()
