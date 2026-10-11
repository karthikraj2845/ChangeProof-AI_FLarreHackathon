from typing import Optional, Set
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.graph.service import InsuranceDependencyGraphService

router = APIRouter(prefix="/graph", tags=["Dependency Graph"])


@router.get("")
def get_graph(
    highlight: Optional[str] = Query(None, description="Comma-separated node IDs to highlight"),
    db: Session = Depends(get_db)
):
    graph_svc = InsuranceDependencyGraphService(db)
    highlight_set: Set[str] = set()
    if highlight:
        highlight_set = set(h.strip() for h in highlight.split(",") if h.strip())
    else:
        # Default highlight active path
        highlight_set = {
            "ART-CR-001", "ART-VER-1.1", "ART-RULE-001", "ART-REQ-001",
            "ART-CFG-001", "ART-SVC-ELIGIBILITY", "ART-SVC-RATING", "ART-TEST-SUITE"
        }

    flow_data = graph_svc.to_react_flow_elements(highlighted_ids=highlight_set)
    return {
        "nodes": flow_data["nodes"],
        "edges": flow_data["edges"],
        "total_nodes": len(flow_data["nodes"]),
        "total_edges": len(flow_data["edges"]),
    }


@router.get("/artifacts/{artifact_id}")
def get_artifact_details(artifact_id: str, db: Session = Depends(get_db)):
    graph_svc = InsuranceDependencyGraphService(db)
    details = graph_svc.get_node_details(artifact_id)
    if not details:
        raise HTTPException(status_code=404, detail="Artifact not found in graph")

    score_data = graph_svc.calculate_impact_score(artifact_id)
    downstream = graph_svc.get_downstream_impacted(artifact_id, max_depth=5)

    return {
        "artifact": details,
        "impact_score_breakdown": score_data,
        "downstream_impacted_count": len(downstream),
        "downstream_artifacts": downstream,
    }
