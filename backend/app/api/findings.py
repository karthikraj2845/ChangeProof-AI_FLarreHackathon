from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.finding import Finding
from app.models.audit import AuditEvent
from app.schemas.api_schemas import FindingUpdateRequest

router = APIRouter(tags=["Findings & Audit"])


@router.get("/findings")
def list_findings(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    change_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Finding)
    if severity:
        query = query.filter(Finding.severity == severity)
    if status:
        query = query.filter(Finding.status == status)
    if change_id:
        query = query.filter(Finding.linked_change_id == change_id)

    findings = query.order_by(Finding.created_at.desc()).all()
    return [
        {
            "id": f.id,
            "finding_type": f.finding_type,
            "severity": f.severity,
            "title": f.title,
            "description": f.description,
            "linked_change_id": f.linked_change_id,
            "linked_rule_id": f.linked_rule_id,
            "linked_rule_version_id": f.linked_rule_version_id,
            "linked_requirement_id": f.linked_requirement_id,
            "linked_test_id": f.linked_test_id,
            "linked_event_id": f.linked_event_id,
            "evidence": f.evidence,
            "status": f.status,
            "created_at": f.created_at,
        }
        for f in findings
    ]


@router.get("/findings/{finding_id}")
def get_finding(finding_id: str, db: Session = Depends(get_db)):
    f = db.query(Finding).filter_by(id=finding_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Finding not found")
    return {
        "id": f.id,
        "finding_type": f.finding_type,
        "severity": f.severity,
        "title": f.title,
        "description": f.description,
        "linked_change_id": f.linked_change_id,
        "linked_rule_id": f.linked_rule_id,
        "linked_rule_version_id": f.linked_rule_version_id,
        "linked_requirement_id": f.linked_requirement_id,
        "linked_test_id": f.linked_test_id,
        "linked_event_id": f.linked_event_id,
        "evidence": f.evidence,
        "status": f.status,
        "created_at": f.created_at,
    }


@router.patch("/findings/{finding_id}")
def update_finding(finding_id: str, payload: FindingUpdateRequest, db: Session = Depends(get_db)):
    f = db.query(Finding).filter_by(id=finding_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Finding not found")

    old_status = f.status
    f.status = payload.status

    unique_id = uuid.uuid4().hex[:6].upper()
    audit = AuditEvent(
        id=f"AUDIT-FND-{finding_id[-6:]}-{unique_id}",
        event_type="FINDING_STATUS_UPDATED",
        entity_type="FINDING",
        entity_id=finding_id,
        actor="UNDERWRITING_ANALYST",
        details={"old_status": old_status, "new_status": payload.status, "note": payload.note},
        timestamp=datetime.now(timezone.utc),
    )
    db.add(audit)
    db.commit()
    db.refresh(f)
    return {"message": "Finding updated", "finding": f}


@router.get("/audit")
def list_audit_events(
    entity_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    query = db.query(AuditEvent)
    if entity_id:
        query = query.filter(AuditEvent.entity_id == entity_id)
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)

    events = query.order_by(AuditEvent.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "actor": e.actor,
            "details": e.details,
            "timestamp": e.timestamp,
        }
        for e in events
    ]
