export interface HealthData {
  status: string;
  version: string;
  environment: string;
  timestamp: string;
  ai_provider_mode: string;
}

export interface DashboardSummary {
  total_change_requests: number;
  pending_reviews: number;
  blocked_releases: number;
  seeded_regressions_detected: number;
  active_rules: number;
  total_artifacts: number;
  open_findings: number;
  recent_workflows: Array<{
    id: string;
    change_request_id: string;
    status: string;
    current_node: string;
    start_time: string;
    completion_time?: string;
  }>;
  findings_by_severity: {
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
  test_metrics: {
    total_suites: number;
    total_test_cases: number;
    coverage_domains: string[];
  };
}

export interface ChangeRequest {
  id: string;
  title: string;
  description: string;
  target_rule_id: string;
  baseline_version_id: string;
  proposed_version_id: string;
  status: string;
  readiness_status: string;
  creator: string;
  created_at: string;
}

export interface ImpactedArtifact {
  artifact_id: string;
  name: string;
  artifact_type: string;
  description: string;
  depth: number;
  is_direct: boolean;
  dependency_path: string[];
  relationship_type: string;
  evidence_source: string;
  confidence: number;
  impact_score: number;
  score_breakdown: {
    total_score: number;
    reach_factor: number;
    criticality_factor: number;
    proximity_factor: number;
    uncertainty_factor: number;
    descendant_count: number;
    node_type: string;
  };
}

export interface TestResultItem {
  test_id: string;
  name: string;
  category: string;
  input_data: Record<string, any>;
  expected_outcome: {
    eligible: boolean;
    discount_percentage: number;
    discount_code?: string;
  };
  baseline_outcome: {
    eligible: boolean;
    discount_percentage: number;
    discount_code?: string;
    explanation: string;
  };
  proposed_outcome: {
    eligible: boolean;
    discount_percentage: number;
    discount_code?: string;
    explanation: string;
  };
  status: 'PASSED' | 'FAILED' | 'REGRESSION' | 'ERROR';
  is_regression: boolean;
  failure_reason?: string;
  latency_ms: number;
  coverage_tags: string[];
}

export interface ReadinessResult {
  status: 'BLOCKED' | 'NEEDS_HUMAN_REVIEW' | 'READY_FOR_REVIEW';
  is_blocked: boolean;
  blockers: string[];
  warnings: string[];
  human_review_triggers: string[];
  evidence_completeness_pct: number;
  recommendation: string;
  requires_human_approval: boolean;
  governance_note: string;
  snapshot_id?: string;
  snapshot_hash?: string;
}

export interface WorkflowState {
  workflow_id: string;
  change_request_id: string;
  user_request: string;
  target_rule_id: string;
  baseline_version_id: string;
  proposed_version_id: string;
  parsed_change?: {
    target_rule: string;
    operation: string;
    condition_field: string;
    description: string;
    ambiguity_flag: boolean;
    confidence: number;
    provider_mode: string;
  };
  domain_context?: {
    rule_name: string;
    rule_type: string;
    requirement_title: string;
    baseline_version: string;
    proposed_version: string;
  };
  impacted_artifacts?: ImpactedArtifact[];
  dependency_paths?: string[][];
  selected_tests?: string[];
  suggested_tests?: Array<{
    id: string;
    name: string;
    category: string;
    reason: string;
    input_data: Record<string, any>;
    expected_outcome: Record<string, any>;
    status: string;
  }>;
  test_results?: TestResultItem[];
  coverage_gaps?: string[];
  readiness_result?: ReadinessResult;
  human_review_decision?: {
    reviewer: string;
    action: string;
    justification: string;
    timestamp: string;
  };
  current_stage: string;
  status: string;
  errors?: string[];
  warnings?: string[];
}

export interface Finding {
  id: string;
  finding_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  description: string;
  linked_change_id?: string;
  linked_rule_id?: string;
  linked_rule_version_id?: string;
  linked_requirement_id?: string;
  linked_test_id?: string;
  linked_event_id?: string;
  evidence: Record<string, any>;
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED' | 'SUPPRESSED';
  created_at: string;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  actor: string;
  details: Record<string, any>;
  timestamp: string;
}
