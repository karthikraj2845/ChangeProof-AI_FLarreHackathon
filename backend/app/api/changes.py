from datetime import datetime, timezone
import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.change import ChangeRequest
from app.models.audit import AuditEvent
from app.graph.service import InsuranceDependencyGraphService
from app.testing.runner import RegressionTestRunner
from app.services.readiness_service import DeterministicReadinessPolicy
from app.schemas.api_schemas import (
    ChangeRequestCreateRequest,
    HumanReviewDecisionRequest,
)

router = APIRouter(prefix="/changes", tags=["Change Requests"])


@router.get("")
def list_changes(db: Session = Depends(get_db)):
    crs = db.query(ChangeRequest).order_by(ChangeRequest.created_at.desc()).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "target_rule_id": c.target_rule_id,
            "baseline_version_id": c.baseline_version_id,
            "proposed_version_id": c.proposed_version_id,
            "status": c.status,
            "readiness_status": c.readiness_status,
            "creator": c.creator,
            "created_at": c.created_at,
        }
        for c in crs
    ]


@router.post("")
def create_change(payload: ChangeRequestCreateRequest, db: Session = Depends(get_db)):
    cr_id = f"CR-2026-{uuid.uuid4().hex[:4].upper()}"
    cr = ChangeRequest(
        id=cr_id,
        title=payload.title,
        description=payload.description,
        target_rule_id=payload.target_rule_id,
        baseline_version_id=payload.baseline_version_id,
        proposed_version_id=payload.proposed_version_id,
        creator=payload.creator,
        status="SUBMITTED",
        readiness_status="PENDING",
    )
    db.add(cr)
    
    audit = AuditEvent(
        id=f"AUDIT-CR-{cr_id}",
        event_type="CHANGE_CREATED",
        entity_type="CHANGE_REQUEST",
        entity_id=cr_id,
        actor=payload.creator,
        details={"title": payload.title, "rule": payload.target_rule_id},
        timestamp=datetime.now(timezone.utc),
    )
    db.add(audit)
    db.commit()
    db.refresh(cr)
    return cr


@router.get("/{change_id}")
def get_change(change_id: str, db: Session = Depends(get_db)):
    cr = db.query(ChangeRequest).filter_by(id=change_id).first()
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")
    return {
        "id": cr.id,
        "title": cr.title,
        "description": cr.description,
        "target_rule_id": cr.target_rule_id,
        "baseline_version_id": cr.baseline_version_id,
        "proposed_version_id": cr.proposed_version_id,
        "status": cr.status,
        "readiness_status": cr.readiness_status,
        "readiness_details": cr.readiness_details,
        "parsed_change": cr.parsed_change_json,
        "creator": cr.creator,
        "created_at": cr.created_at,
    }


@router.post("/{change_id}/analyze-impact")
def analyze_impact(change_id: str, db: Session = Depends(get_db)):
    cr = db.query(ChangeRequest).filter_by(id=change_id).first()
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")

    graph_svc = InsuranceDependencyGraphService(db)
    impacted = graph_svc.get_downstream_impacted("ART-VER-1.1", max_depth=6)
    if not impacted:
        impacted = graph_svc.get_downstream_impacted("ART-RULE-001", max_depth=6)

    paths = graph_svc.find_all_paths("ART-CR-001", "ART-TEST-SUITE", max_depth=6)
    return {
        "change_id": change_id,
        "impacted_artifacts": impacted,
        "dependency_paths": paths,
        "total_impacted": len(impacted),
    }


@router.get("/{change_id}/impact")
def get_impact(change_id: str, db: Session = Depends(get_db)):
    return analyze_impact(change_id, db)


@router.post("/{change_id}/run-tests")
def run_tests_for_change(change_id: str, db: Session = Depends(get_db)):
    cr = db.query(ChangeRequest).filter_by(id=change_id).first()
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")

    test_ids = [
        "TEST-SD-001", "TEST-SD-002", "TEST-SD-003", "TEST-SD-004",
        "TEST-SD-005", "TEST-SD-006", "TEST-SD-007", "TEST-SD-008"
    ]

    res = RegressionTestRunner.run_tests(
        db=db,
        test_ids=test_ids,
        baseline_version_id=cr.baseline_version_id,
        proposed_version_id=cr.proposed_version_id,
    )
    return res


@router.get("/{change_id}/test-results")
def get_test_results_for_change(change_id: str, db: Session = Depends(get_db)):
    return run_tests_for_change(change_id, db)


@router.get("/{change_id}/readiness")
def get_readiness(change_id: str, db: Session = Depends(get_db)):
    cr = db.query(ChangeRequest).filter_by(id=change_id).first()
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")

    # Run tests to evaluate readiness
    test_run = run_tests_for_change(change_id, db)
    graph_svc = InsuranceDependencyGraphService(db)
    impacted = graph_svc.get_downstream_impacted("ART-VER-1.1", max_depth=6)

    readiness = DeterministicReadinessPolicy.evaluate(
        test_summary=test_run,
        impacted_artifacts=impacted,
        baseline_version_id=cr.baseline_version_id,
        proposed_version_id=cr.proposed_version_id,
    )

    cr.readiness_status = readiness["status"]
    cr.readiness_details = readiness
    db.commit()

    return readiness


@router.post("/{change_id}/approve")
def approve_change(change_id: str, payload: HumanReviewDecisionRequest, db: Session = Depends(get_db)):
    cr = db.query(ChangeRequest).filter_by(id=change_id).first()
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")

    if cr.readiness_status == "BLOCKED":
        raise HTTPException(
            status_code=400,
            detail="Cannot approve change: Release is strictly BLOCKED by deterministic policy due to critical regressions."
        )

    cr.status = "APPROVED"
    now = datetime.now(timezone.utc)
    audit = AuditEvent(
        id=f"AUDIT-APP-{uuid.uuid4().hex[:6]}",
        event_type="HUMAN_APPROVAL",
        entity_type="CHANGE_REQUEST",
        entity_id=change_id,
        actor=payload.reviewer,
        details={"justification": payload.justification},
        timestamp=now,
    )
    db.add(audit)
    db.commit()

    return {"message": "Change request approved by reviewer.", "status": cr.status}


@router.post("/{change_id}/reject")
def reject_change(change_id: str, payload: HumanReviewDecisionRequest, db: Session = Depends(get_db)):
    cr = db.query(ChangeRequest).filter_by(id=change_id).first()
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")

    cr.status = "REJECTED"
    now = datetime.now(timezone.utc)
    audit = AuditEvent(
        id=f"AUDIT-REJ-{uuid.uuid4().hex[:6]}",
        event_type="HUMAN_REJECTION",
        entity_type="CHANGE_REQUEST",
        entity_id=change_id,
        actor=payload.reviewer,
        details={"justification": payload.justification},
        timestamp=now,
    )
    db.add(audit)
    db.commit()

    return {"message": "Change request rejected by reviewer.", "status": cr.status}
