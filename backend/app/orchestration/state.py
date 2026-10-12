from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class WorkflowState(TypedDict, total=False):
    workflow_id: str
    change_request_id: str
    user_request: str
    target_rule_id: str
    baseline_version_id: str
    proposed_version_id: str
    parsed_change: Dict[str, Any]
    domain_context: Dict[str, Any]
    impacted_artifacts: List[Dict[str, Any]]
    dependency_paths: List[List[str]]
    selected_tests: List[str]
    suggested_tests: List[Dict[str, Any]]
    test_results: List[Dict[str, Any]]
    coverage_gaps: List[str]
    risk_findings: List[Dict[str, Any]]
    readiness_result: Dict[str, Any]
    snapshot_id: Optional[str]
    snapshot_hash: Optional[str]
    human_review_decision: Optional[Dict[str, Any]]
    verification_result: Optional[Dict[str, Any]]
    current_stage: str
    status: str  # RUNNING, PAUSED_FOR_REVIEW, NEEDS_HUMAN_REVIEW, READY_FOR_REVIEW, REJECTED, REVISION_REQUIRED, BLOCKED, COMPLETED, FAILED
    errors: List[str]
    warnings: List[str]
    execution_metadata: Dict[str, Any]
