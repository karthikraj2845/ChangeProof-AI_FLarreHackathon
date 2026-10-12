import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.event import ObservedEvent
from app.rules.engine import DeterministicRuleEngine
from app.models.rule import RuleVersion
from app.verification.intent_guard import IntentGuardVerifier
from app.schemas.api_schemas import SimulateTransactionRequest

router = APIRouter(prefix="/verification", tags=["IntentGuard Verification"])


@router.post("/simulate")
def simulate_transaction(payload: SimulateTransactionRequest, db: Session = Depends(get_db)):
    txn_id = payload.transaction_id or f"TXN-{uuid.uuid4().hex[:6].upper()}"

    # Construct transaction payload
    txn_input = {
        "jurisdiction": payload.jurisdiction,
        "driver_risk_score": payload.driver_risk_score,
        "vehicle_category": payload.vehicle_category,
        "policy_active": payload.policy_active,
    }

    # Simulate what the deployed version produces:
    deployed_rv = db.query(RuleVersion).filter_by(id=payload.simulated_deployed_version_id).first()
    if not deployed_rv:
        raise HTTPException(status_code=400, detail="Simulated deployed rule version not found.")

    deployed_eval = DeterministicRuleEngine.evaluate(
        deployed_rv.rule_definition,
        txn_input,
        version_id=payload.simulated_deployed_version_id,
    )

    observed_outcome = {
        "eligible": deployed_eval.eligible,
        "discount_percentage": deployed_eval.discount_percentage,
        "discount_code": deployed_eval.discount_code,
        "explanation": deployed_eval.explanation,
    }

    # Execute IntentGuard verification against approved reference version
    verification_res = IntentGuardVerifier.verify_event(
        db=db,
        transaction_id=txn_id,
        input_data=txn_input,
        observed_outcome=observed_outcome,
        reported_version_id=payload.simulated_deployed_version_id,
        approved_reference_version_id=payload.approved_reference_version_id,
        linked_change_id=payload.linked_change_id,
        expected_version_hash=payload.expected_version_hash,
        strict_mode=payload.strict_mode,
    )

    return verification_res


@router.get("/events")
def list_observed_events(db: Session = Depends(get_db)):
    events = db.query(ObservedEvent).order_by(ObservedEvent.created_at.desc()).limit(20).all()
    return [
        {
            "id": e.id,
            "transaction_identifier": e.transaction_identifier,
            "event_type": e.event_type,
            "input_data": e.input_data,
            "observed_outcome": e.observed_outcome,
            "reported_rule_version": e.reported_rule_version,
            "simulated": e.simulated,
            "created_at": e.created_at,
        }
        for e in events
    ]
