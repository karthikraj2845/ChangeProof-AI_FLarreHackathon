from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.workflow import WorkflowRun
from app.models.audit import AuditEvent
from app.orchestration.runner import WorkflowRunner
from app.schemas.api_schemas import (
    StartWorkflowRequest,
    ResumeWorkflowRequest,
)

router = APIRouter(prefix="/workflows", tags=["Agent Workflows"])


@router.post("/change-assurance")
def start_change_assurance(payload: StartWorkflowRequest, db: Session = Depends(get_db)):
    try:
        result = WorkflowRunner.start_change_assurance(
            db=db,
            change_request_id=payload.change_request_id,
            user_request=payload.user_request,
        )
        return {
            "message": "Change assurance workflow started and executed.",
            "workflow_id": result.get("workflow_id"),
            "status": result.get("status"),
            "current_stage": result.get("current_stage"),
            "state": result,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workflow_id}")
def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    wf = db.query(WorkflowRun).filter_by(id=workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return {
        "id": wf.id,
        "change_request_id": wf.change_request_id,
        "workflow_type": wf.workflow_type,
        "status": wf.status,
        "current_node": wf.current_node,
        "start_time": wf.start_time,
        "completion_time": wf.completion_time,
        "state": wf.state_json,
    }


@router.get("/{workflow_id}/events")
def get_workflow_events(workflow_id: str, db: Session = Depends(get_db)):
    wf = db.query(WorkflowRun).filter_by(id=workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow run not found")

    events = db.query(AuditEvent).filter(
        (AuditEvent.entity_id == workflow_id) |
        (AuditEvent.entity_id == wf.change_request_id)
    ).order_by(AuditEvent.timestamp.asc()).all()

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


@router.post("/{workflow_id}/resume")
def resume_workflow(workflow_id: str, payload: ResumeWorkflowRequest, db: Session = Depends(get_db)):
    try:
        res = WorkflowRunner.resume_with_review(
            db=db,
            workflow_id=workflow_id,
            reviewer=payload.reviewer,
            action=payload.action,
            justification=payload.justification,
            snapshot_id=payload.snapshot_id,
        )
        return {
            "message": f"Workflow resumed with review decision: {payload.action}",
            "status": res.get("status"),
            "state": res,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
