from datetime import datetime, timezone
import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.change import ChangeRequest
from app.models.audit import AuditEvent
from app.models.test import RegressionTest
from app.graph.service import InsuranceDependencyGraphService
from app.testing.runner import RegressionTestRunner
from app.services.readiness_service import DeterministicReadinessPolicy
from app.services.snapshot_service import SnapshotService
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
        id=f"AUDIT-CR-{cr_id}-{uuid.uuid4().hex[:4].upper()}",
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

    # Dynamically find starting artifact node
    source_art = graph_svc.find_artifact_for_entity(cr.proposed_version_id)
    if not source_art:
        source_art = graph_svc.find_artifact_for_entity(cr.target_rule_id)
    if not source_art:
        source_art = "ART-VER-1.1" if "ART-VER-1.1" in graph_svc.graph else list(graph_svc.graph.nodes)[0]

    impacted = graph_svc.get_downstream_impacted(source_art, max_depth=6)

    # Dynamically find paths from change request to regression tests
    cr_art = graph_svc.find_artifact_for_entity(change_id) or "ART-CR-001"
    paths = []
    test_nodes = [n for n, d in graph_svc.graph.nodes(data=True) if d.get("artifact_type") in ["REGRESSION_TEST", "TEST_SUITE"]]
    for tn in test_nodes:
        found_paths = graph_svc.find_all_paths(cr_art, tn, max_depth=6)
        if found_paths:
            paths.extend(found_paths)

    return {
        "change_id": change_id,
        "source_artifact": source_art,
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

    # Discover linked tests dynamically via graph
    graph_svc = InsuranceDependencyGraphService(db)
    source_art = graph_svc.find_artifact_for_entity(cr.proposed_version_id) or graph_svc.find_artifact_for_entity(cr.target_rule_id) or "ART-VER-1.1"
    impacted = graph_svc.get_downstream_impacted(source_art, max_depth=6)
    impacted_ids = [item["artifact_id"] for item in impacted]

    # Resolve linked tests from DB
    db_tests = db.query(RegressionTest).filter(RegressionTest.linked_rule_id == cr.target_rule_id).all()
    test_ids = [t.id for t in db_tests]

    # Merge mandatory safety/invariant tests
    safety_tests = ["TEST-SD-001", "TEST-SD-002", "TEST-SD-007"]
    candidate_tests = list(dict.fromkeys(test_ids + safety_tests))
    valid_tests = db.query(RegressionTest.id).filter(RegressionTest.id.in_(candidate_tests)).all()
    final_test_ids = sorted([t[0] for t in valid_tests])

    if not final_test_ids:
        final_test_ids = [t.id for t in db.query(RegressionTest).all()]

    res = RegressionTestRunner.run_tests(
        db=db,
        test_ids=final_test_ids,
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

    # Run tests to evaluate readiness dynamically
    test_run = run_tests_for_change(change_id, db)
    graph_svc = InsuranceDependencyGraphService(db)
    source_art = graph_svc.find_artifact_for_entity(cr.proposed_version_id) or graph_svc.find_artifact_for_entity(cr.target_rule_id) or "ART-VER-1.1"
    impacted = graph_svc.get_downstream_impacted(source_art, max_depth=6)

    readiness = DeterministicReadinessPolicy.evaluate(
        test_summary=test_run,
        impacted_artifacts=impacted,
        baseline_version_id=cr.baseline_version_id,
        proposed_version_id=cr.proposed_version_id,
    )

    # Generate or update EvidenceSnapshot
    snapshot = SnapshotService.create_snapshot(
        db=db,
        change_request_id=cr.id,
        workflow_run_id=None,
        target_rule_id=cr.target_rule_id,
        baseline_version_id=cr.baseline_version_id,
        proposed_version_id=cr.proposed_version_id,
        test_summary=test_run,
        impacted_artifacts=impacted,
        selected_test_ids=[r["test_id"] for r in test_run.get("results", [])],
        readiness_result=readiness,
    )

    cr.readiness_status = readiness["status"]
    cr.readiness_details = {**readiness, "snapshot_id": snapshot.id, "snapshot_hash": snapshot.snapshot_hash}
    db.commit()

    return {**readiness, "snapshot_id": snapshot.id, "snapshot_hash": snapshot.snapshot_hash}


@router.post("/{change_id}/approve")
def approve_change(change_id: str, payload: HumanReviewDecisionRequest, db: Session = Depends(get_db)):
    cr = db.query(ChangeRequest).filter_by(id=change_id).first()
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")

    if cr.readiness_status == "BLOCKED":
        raise HTTPException(
            status_code=400,
            detail="GOVERNANCE VIOLATION: Cannot approve change. Release is strictly BLOCKED by deterministic policy due to critical regressions."
        )

    # Verify Snapshot Integrity if present in readiness details
    if cr.readiness_details and cr.readiness_details.get("snapshot_id"):
        validity = SnapshotService.verify_snapshot_validity(db, cr.readiness_details["snapshot_id"])
        if not validity["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"STALE EVIDENCE: {validity.get('reason')}"
            )

    cr.status = "APPROVED"
    now = datetime.now(timezone.utc)
    audit = AuditEvent(
        id=f"AUDIT-APP-{uuid.uuid4().hex[:6]}-{uuid.uuid4().hex[:4].upper()}",
        event_type="HUMAN_APPROVAL",
        entity_type="CHANGE_REQUEST",
        entity_id=change_id,
        actor=payload.reviewer,
        details={"justification": payload.justification, "snapshot_id": cr.readiness_details.get("snapshot_id") if cr.readiness_details else None},
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
        id=f"AUDIT-REJ-{uuid.uuid4().hex[:6]}-{uuid.uuid4().hex[:4].upper()}",
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
