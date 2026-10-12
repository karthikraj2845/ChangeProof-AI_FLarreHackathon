from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# Health & Summary
class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: datetime
    ai_provider_mode: str


class DashboardSummaryResponse(BaseModel):
    total_change_requests: int
    pending_reviews: int
    blocked_releases: int
    seeded_regressions_detected: int
    active_rules: int
    total_artifacts: int
    open_findings: int
    recent_workflows: List[Dict[str, Any]]
    findings_by_severity: Dict[str, int]
    test_metrics: Dict[str, Any]


# Rules
class RuleVersionCreateRequest(BaseModel):
    version: str
    description: str
    rule_definition: Dict[str, Any]
    product_scope: str = "PERSONAL_AUTO"
    jurisdiction_scope: Optional[List[str]] = None


# Change Requests
class ChangeRequestCreateRequest(BaseModel):
    title: str
    description: str
    target_rule_id: str = "RULE-SAFE-DRIVER"
    baseline_version_id: str = "RULE-SAFE-DRIVER-v1.0"
    proposed_version_id: str = "RULE-SAFE-DRIVER-v1.1-proposed"
    creator: str = "underwriting_analyst"


# Workflow
class StartWorkflowRequest(BaseModel):
    change_request_id: str = "CR-2026-001"
    user_request: Optional[str] = None


class ResumeWorkflowRequest(BaseModel):
    reviewer: str = "Underwriting Director"
    action: str = "APPROVE"  # APPROVE, REJECT, REQUEST_MORE_TESTS, REVISION_REQUIRED
    justification: str
    snapshot_id: Optional[str] = None
    snapshot_hash: Optional[str] = None


# Human Review
class HumanReviewDecisionRequest(BaseModel):
    reviewer: str
    justification: str
    snapshot_id: Optional[str] = None
    snapshot_hash: Optional[str] = None


# Verification & Simulation
class SimulateTransactionRequest(BaseModel):
    transaction_id: Optional[str] = None
    jurisdiction: str = "NV"
    driver_risk_score: float = 15.0
    vehicle_category: str = "SEDAN"
    policy_active: bool = True
    approved_reference_version_id: str = "RULE-SAFE-DRIVER-v1.0"
    simulated_deployed_version_id: str = "RULE-SAFE-DRIVER-v1.1-proposed"
    linked_change_id: str = "CR-2026-001"
    expected_version_hash: Optional[str] = None
    strict_mode: bool = False


# Finding Update
class FindingUpdateRequest(BaseModel):
    status: str  # OPEN, ACKNOWLEDGED, RESOLVED, SUPPRESSED
    note: Optional[str] = None
