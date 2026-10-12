from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.event import ObservedEvent
from app.models.finding import Finding
from app.models.rule import RuleVersion
from app.models.test import RegressionTest
from app.models.requirement import Requirement
from app.models.audit import AuditEvent
from app.models.snapshot import EvidenceSnapshot
from app.rules.engine import DeterministicRuleEngine
from app.services.snapshot_service import SnapshotService


class IntentGuardVerifier:
    """
    IntentGuard post-deployment event verification engine.
    Compares simulated/observed production transactions against explicitly approved reference rule versions.
    Verifies reference version approval status and cryptographic content hashes.
    Dynamically traces linked requirements and failing tests, generating immutable audit findings upon deviation.
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
        linked_change_id: Optional[str] = None,
        expected_version_hash: Optional[str] = None,
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
            db.commit()
            return {
                "status": "UNVERIFIABLE",
                "transaction_id": transaction_id,
                "summary": f"Cannot verify transaction: Reference version '{approved_reference_version_id}' not found in registry.",
                "finding_created": False,
            }

        # 3. Verify approval status of the reference version
        if approved_rv.status != "APPROVED":
            db.commit()
            return {
                "status": "UNVERIFIABLE",
                "transaction_id": transaction_id,
                "summary": f"Governance Error: Reference version '{approved_reference_version_id}' is in status '{approved_rv.status}', NOT 'APPROVED'. Post-deployment verification requires an approved reference.",
                "finding_created": False,
            }

        # 4. Verify cryptographic version content hash if provided
        computed_hash = SnapshotService.compute_version_hash(approved_rv.rule_definition)
        if expected_version_hash and computed_hash != expected_version_hash:
            db.commit()
            return {
                "status": "UNVERIFIABLE",
                "transaction_id": transaction_id,
                "summary": f"Security Error: Reference version '{approved_reference_version_id}' hash mismatch! Expected {expected_version_hash}, found {computed_hash}.",
                "finding_created": False,
            }

        # 5. Calculate authoritative expected outcome using deterministic rule engine
        expected_eval = DeterministicRuleEngine.evaluate(
            approved_rv.rule_definition,
            input_data,
            version_id=approved_reference_version_id,
        )

        expected_eligible = expected_eval.eligible
        expected_discount = float(expected_eval.discount_percentage)

        # Safely parse observed values
        try:
            observed_eligible = bool(observed_outcome.get("eligible", False))
            observed_discount = float(observed_outcome.get("discount_percentage", 0.0))
        except (ValueError, TypeError):
            db.commit()
            return {
                "status": "UNVERIFIABLE",
                "transaction_id": transaction_id,
                "summary": "Malformed observed outcome data: invalid eligibility or discount format.",
                "finding_created": False,
            }

        # 6. Compare expected vs observed
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
                f"Jurisdiction '{input_data.get('jurisdiction')}' received unexpected outcome!"
            )
            summary = description

            # Dynamically resolve linked requirement from rule's tests, graph, or domain
            linked_req_id = None
            candidate_tests = db.query(RegressionTest).filter(
                RegressionTest.linked_rule_id == approved_rv.rule_id
            ).all()

            # First look for test-associated requirement
            for t in candidate_tests:
                if t.linked_requirement_id:
                    linked_req_id = t.linked_requirement_id
                    break

            # Fallback to requirement matching product scope or rule domain
            if not linked_req_id:
                req = db.query(Requirement).filter(
                    (Requirement.domain.ilike("%Auto%")) |
                    (Requirement.title.ilike(f"%{approved_rv.rule.name if approved_rv.rule else 'Safe Driver'}%"))
                ).first()
                if req:
                    linked_req_id = req.id
            for t in candidate_tests:
                # Require actual scenario alignment: matching jurisdiction or failure category
                if t.input_data.get("jurisdiction") and t.input_data.get("jurisdiction") == input_data.get("jurisdiction"):
                    matching_test = t
                    break
            # Do NOT attach an arbitrary unrelated test if no match exists
            linked_test_id = matching_test.id if matching_test else None

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
                linked_requirement_id=linked_req_id,
                linked_test_id=linked_test_id,
                linked_event_id=event_record.id,
                evidence={
                    "transaction_id": transaction_id,
                    "input_data": input_data,
                    "approved_reference_version": approved_reference_version_id,
                    "approved_version_hash": computed_hash,
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
                        "variance": round(observed_discount - expected_discount, 2),
                    }
                },
                status="OPEN",
                created_at=now,
            )
            db.add(finding_record)

            # Record audit event with unique ID
            audit = AuditEvent(
                id=f"AUDIT-DEV-{unique_suffix}-{uuid.uuid4().hex[:4].upper()}",
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
                f"Observed behavior matches expected underwriting specifications ({observed_discount}% discount)."
            )

        db.commit()

        return {
            "status": status,
            "transaction_id": transaction_id,
            "approved_reference_version": approved_reference_version_id,
            "reference_version_hash": computed_hash,
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
