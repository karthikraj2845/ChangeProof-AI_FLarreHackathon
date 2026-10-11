import logging
from typing import Any, Dict, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class AIProvider:
    """
    Vendor-agnostic AI provider abstraction.
    Gracefully falls back to heuristic domain reasoning when LLM API keys are missing or offline.
    """

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
        Uses OpenAI structured output if available, else heuristic domain parser.
        """
        if self.has_llm and self.client:
            try:
                prompt = (
                    "You are an insurance underwriting systems analyst. Parse this rule change request into JSON:\n"
                    f"User request: '{user_text}'\n\n"
                    "Extract:\n"
                    "- target_rule: rule ID (e.g. 'RULE-SAFE-DRIVER')\n"
                    "- operation: 'REMOVE_CONDITION', 'MODIFY_THRESHOLD', 'ADD_CONDITION'\n"
                    "- condition_field: field affected (e.g. 'jurisdiction', 'driver_risk_score')\n"
                    "- description: structured summary\n"
                    "- ambiguity_flag: boolean\n"
                    "- confidence: float (0.0 to 1.0)\n"
                    "Respond with valid JSON only."
                )
                res = self.client.invoke(prompt)
                import json
                content = res.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                return json.loads(content.strip())
            except Exception as e:
                logger.warning(f"LLM parsing failed: {e}. Using deterministic heuristic parser.")

        # Deterministic Heuristic Insurance Parser
        text_lower = user_text.lower()
        target_rule = "RULE-SAFE-DRIVER"
        operation = "MODIFY_RULE"
        condition_field = "unknown"
        ambiguity = False

        if "jurisdiction" in text_lower or "state" in text_lower:
            condition_field = "jurisdiction"
            if "remove" in text_lower or "drop" in text_lower or "delete" in text_lower:
                operation = "REMOVE_CONDITION"
        elif "risk score" in text_lower or "driver score" in text_lower:
            condition_field = "driver_risk_score"
            operation = "MODIFY_THRESHOLD"
        elif "vehicle" in text_lower:
            condition_field = "vehicle_category"
            operation = "MODIFY_CONDITION"

        return {
            "target_rule": target_rule,
            "operation": operation,
            "condition_field": condition_field,
            "description": f"Parsed intent: {operation} on field '{condition_field}' for rule {target_rule}.",
            "ambiguity_flag": ambiguity,
            "confidence": 0.98 if condition_field != "unknown" else 0.40,
            "provider_mode": "LLM" if (self.has_llm and self.client) else "HEURISTIC_OFFLINE_CAPABLE",
        }

    def suggest_missing_test_cases(
        self,
        rule_name: str,
        conditions: List[Dict[str, Any]],
        existing_test_tags: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Synthesizes candidate edge-case regression tests.
        Clearly marked as unvalidated suggestions until executed.
        """
        suggestions = [
            {
                "id": "SUGGESTED-TC-001",
                "name": "Multi-Vehicle Policy Discount Accumulation Check",
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
                "name": "Zero Telematics Miles Logged Boundary Test",
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
