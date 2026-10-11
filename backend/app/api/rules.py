from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.rule import Rule, RuleVersion
from app.rules.engine import DeterministicRuleEngine
from app.schemas.api_schemas import RuleVersionCreateRequest

router = APIRouter(prefix="/rules", tags=["Insurance Rules"])


@router.get("")
def list_rules(db: Session = Depends(get_db)):
    rules = db.query(Rule).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "rule_type": r.rule_type,
            "version_count": len(r.versions),
            "versions": [{"id": v.id, "version": v.version, "status": v.status} for v in r.versions],
        }
        for r in rules
    ]


@router.get("/{rule_id}")
def get_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.query(Rule).filter_by(id=rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {
        "id": rule.id,
        "name": rule.name,
        "description": rule.description,
        "rule_type": rule.rule_type,
        "versions": [
            {
                "id": v.id,
                "version": v.version,
                "status": v.status,
                "is_immutable": v.is_immutable,
                "product_scope": v.product_scope,
                "created_at": v.created_at,
            }
            for v in rule.versions
        ],
    }


@router.get("/{rule_id}/versions")
def get_rule_versions(rule_id: str, db: Session = Depends(get_db)):
    versions = db.query(RuleVersion).filter_by(rule_id=rule_id).all()
    return [
        {
            "id": v.id,
            "version": v.version,
            "description": v.description,
            "status": v.status,
            "is_immutable": v.is_immutable,
            "product_scope": v.product_scope,
            "jurisdiction_scope": v.jurisdiction_scope,
            "rule_definition": v.rule_definition,
            "created_at": v.created_at,
            "approved_at": v.approved_at,
        }
        for v in versions
    ]


@router.post("/{rule_id}/versions")
def create_rule_version(rule_id: str, payload: RuleVersionCreateRequest, db: Session = Depends(get_db)):
    rule = db.query(Rule).filter_by(id=rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    version_id = f"{rule_id}-v{payload.version}"
    existing = db.query(RuleVersion).filter_by(id=version_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Rule version already exists")

    rv = RuleVersion(
        id=version_id,
        rule_id=rule_id,
        version=payload.version,
        description=payload.description,
        rule_definition=payload.rule_definition,
        status="PROPOSED",
        is_immutable=False,
        product_scope=payload.product_scope,
        jurisdiction_scope=payload.jurisdiction_scope,
    )
    db.add(rv)
    db.commit()
    db.refresh(rv)
    return {"message": "Rule version created", "version_id": rv.id, "status": rv.status}


@router.post("/{rule_id}/versions/{version_id}/evaluate")
def evaluate_version(rule_id: str, version_id: str, data: Dict[str, Any], db: Session = Depends(get_db)):
    rv = db.query(RuleVersion).filter_by(id=version_id, rule_id=rule_id).first()
    if not rv:
        raise HTTPException(status_code=404, detail="Rule version not found")

    result = DeterministicRuleEngine.evaluate(rv.rule_definition, data, version_id=version_id)
    return result.model_dump()
