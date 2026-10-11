from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.event import ObservedEvent
from app.models.finding import Finding
from app.models.rule import RuleVersion
from app.models.audit import AuditEvent
from app.rules.engine import DeterministicRuleEngine


class IntentGuardVerifier:
    """
    IntentGuard post-deployment event verification engine.
    Compares simulated/observed production transactions against explicitly approved reference rule versions.
    Generates traced audit findings upon detecting behavioral deviations.
    """

    @classmethod
    def verify_event(
        cls,
        db: Session,
        transaction_id: str,
        input_data: Dict[str, Any],
        observed_outcome: Dict[str, Any],
        reported_version_id: str,
        approved_reference_version_id: str,
        linked_change_id: Optional[str] = "CR-2026-001",
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        unique_suffix = uuid.uuid4().hex[:6].upper()

        # 1. Store observed transaction
        event_record = ObservedEvent(
            id=f"EVT-{transaction_id}-{unique_suffix}",
            transaction_identifier=transaction_id,
            event_type="QUOTE_RATING_REQUEST",
            input_data=input_data,
            observed_outcome=observed_outcome,
            reported_rule_version=reported_version_id,
            simulated=True,
            created_at=now,
        )
        db.add(event_record)

        # 2. Retrieve approved reference version
        approved_rv = db.query(RuleVersion).filter_by(id=approved_reference_version_id).first()
        if not approved_rv:
            status = "UNVERIFIABLE"
            summary = f"Cannot verify transaction: Approved reference version '{approved_reference_version_id}' not found."
            db.commit()
            return {
                "status": status,
                "transaction_id": transaction_id,
                "summary": summary,
                "finding_created": False,
            }

        # 3. Calculate authoritative expected outcome using deterministic rule engine
        expected_eval = DeterministicRuleEngine.evaluate(
            approved_rv.rule_definition,
            input_data,
            version_id=approved_reference_version_id,
        )

        expected_eligible = expected_eval.eligible
        expected_discount = expected_eval.discount_percentage

        observed_eligible = observed_outcome.get("eligible", False)
        observed_discount = observed_outcome.get("discount_percentage", 0.0)

        # 4. Compare expected vs observed
        is_deviation = (
            expected_eligible != observed_eligible or
            abs(expected_discount - observed_discount) > 0.01
        )

        finding_record = None
        if is_deviation:
            status = "DEVIATION"
            title = f"IntentGuard Alert: Deployed transaction deviated from approved rule {approved_reference_version_id}"
            description = (
                f"Transaction {transaction_id} reported deployed version '{reported_version_id}' awarded "
                f"{observed_discount}% discount (eligible={observed_eligible}), but approved reference version "
                f"'{approved_reference_version_id}' dictates {expected_discount}% discount (eligible={expected_eligible}). "
                f"Driver in state '{input_data.get('jurisdiction')}' received unauthorized discount!"
            )
            summary = description

            # Create traceable finding
            finding_record = Finding(
                id=f"FINDING-IG-{unique_suffix}",
                finding_type="DEVIATION",
                severity="CRITICAL",
                title=title,
                description=description,
                linked_change_id=linked_change_id,
                linked_rule_id=approved_rv.rule_id,
                linked_rule_version_id=reported_version_id,
                linked_requirement_id="REQ-AUTO-DISC-001",
                linked_test_id="TEST-SD-002",
                linked_event_id=event_record.id,
                evidence={
                    "transaction_id": transaction_id,
                    "input_data": input_data,
                    "approved_reference_version": approved_reference_version_id,
                    "deployed_version": reported_version_id,
                    "expected_outcome": {
                        "eligible": expected_eligible,
                        "discount_percentage": expected_discount,
                        "explanation": expected_eval.explanation,
                    },
                    "observed_outcome": observed_outcome,
                    "discrepancy": {
                        "expected_discount": expected_discount,
                        "observed_discount": observed_discount,
                        "variance": observed_discount - expected_discount,
                    }
                },
                status="OPEN",
                created_at=now,
            )
            db.add(finding_record)

            # Record audit event
            audit = AuditEvent(
                id=f"AUDIT-DEV-{unique_suffix}",
                event_type="INTENTGUARD_DEVIATION_DETECTED",
                entity_type="FINDING",
                entity_id=finding_record.id,
                actor="INTENTGUARD_AGENT",
                details={"transaction_id": transaction_id, "deviation": summary},
                timestamp=now,
            )
            db.add(audit)

        else:
            status = "VERIFIED"
            summary = (
                f"Transaction {transaction_id} verified against approved version {approved_reference_version_id}. "
                f"Observed behavior exactly matches expected underwriting specifications ({observed_discount}% discount)."
            )

        db.commit()

        return {
            "status": status,
            "transaction_id": transaction_id,
            "approved_reference_version": approved_reference_version_id,
            "reported_version": reported_version_id,
            "input_data": input_data,
            "expected_outcome": {
                "eligible": expected_eligible,
                "discount_percentage": expected_discount,
                "explanation": expected_eval.explanation,
            },
            "observed_outcome": observed_outcome,
            "is_deviation": is_deviation,
            "summary": summary,
            "finding_id": finding_record.id if finding_record else None,
            "finding": {
                "id": finding_record.id,
                "title": finding_record.title,
                "severity": finding_record.severity,
                "description": finding_record.description,
                "linked_change_id": finding_record.linked_change_id,
                "linked_test_id": finding_record.linked_test_id,
            } if finding_record else None,
        }
