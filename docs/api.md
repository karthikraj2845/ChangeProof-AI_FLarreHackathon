# ChangeProof AI &bull; REST API Specification

Base URL: `http://localhost:8000/api`  
Interactive Swagger Docs: `http://localhost:8000/docs`

---

## 1. Health & Dashboard

### `GET /api/health`
Returns system status, active version, environment, and AI provider mode.

### `GET /api/dashboard/summary`
Returns aggregate statistics:
- Total change requests
- Seeded regressions detected
- Blocked releases
- Open findings by severity
- Recent workflow runs
- Test metrics

### `POST /api/demo/launch`
One-click demo initialization: Resets the SQLite/Postgres database with the pristine motor insurance scenario and runs the complete change assurance workflow.

---

## 2. Rules & Versions

### `GET /api/rules`
Lists all insurance rules and their version count.

### `GET /api/rules/{rule_id}`
Returns rule details and list of registered versions.

### `GET /api/rules/{rule_id}/versions`
Returns all version definitions for a given rule (conditions, actions, status, immutability flag).

### `POST /api/rules/{rule_id}/versions`
Creates a new candidate rule version.

### `POST /api/rules/{rule_id}/versions/{version_id}/evaluate`
Ad-hoc deterministic rule evaluation for inspection.

---

## 3. Change Requests

### `GET /api/changes`
Lists all submitted change requests with current readiness status.

### `POST /api/changes`
Submits a new change proposal.

### `GET /api/changes/{change_id}`
Returns change request details, parsed change structure, and readiness details.

### `POST /api/changes/{change_id}/analyze-impact`
Triggers RuleRipple graph traversal and returns all directly and transitively affected artifacts with blast radius scores.

### `POST /api/changes/{change_id}/run-tests`
Executes regression tests side-by-side against baseline and proposed versions.

### `GET /api/changes/{change_id}/readiness`
Evaluates deterministic readiness policy (BLOCKED, NEEDS_HUMAN_REVIEW, READY_FOR_REVIEW).

### `POST /api/changes/{change_id}/approve`
Submits human approval. Strictly fails if release is BLOCKED by regressions.

### `POST /api/changes/{change_id}/reject`
Submits human rejection with justification.

---

## 4. Agent Workflows

### `POST /api/workflows/change-assurance`
Initiates the 7-stage LangGraph change assurance workflow.
```json
{
  "change_request_id": "CR-2026-001",
  "user_request": "Remove the jurisdiction restriction from the safe-driver discount eligibility rule."
}
```

### `GET /api/workflows/{workflow_id}`
Retrieves persisted workflow state, current node, and status.

### `POST /api/workflows/{workflow_id}/resume`
Resumes a paused workflow run following a human governance decision.

---

## 5. Dependency Graph

### `GET /api/graph`
Returns nodes and edges formatted for React Flow canvas visualization.

### `GET /api/graph/artifacts/{artifact_id}`
Returns detailed artifact metadata, downstream reach, and explainable impact score breakdown.

---

## 6. IntentGuard Verification

### `POST /api/verification/simulate`
Simulates a deployed transaction and verifies observed outcome against the approved reference version.
```json
{
  "transaction_id": "TXN-2026-01",
  "jurisdiction": "NV",
  "driver_risk_score": 15,
  "vehicle_category": "SEDAN",
  "policy_active": true,
  "approved_reference_version_id": "RULE-SAFE-DRIVER-v1.0",
  "simulated_deployed_version_id": "RULE-SAFE-DRIVER-v1.1-proposed"
}
```
**Response:**
```json
{
  "status": "DEVIATION",
  "transaction_id": "TXN-2026-01",
  "is_deviation": true,
  "expected_outcome": {
    "eligible": false,
    "discount_percentage": 0.0
  },
  "observed_outcome": {
    "eligible": true,
    "discount_percentage": 10.0
  },
  "finding_id": "FINDING-IG-01"
}
```

---

## 7. Findings & Audit

### `GET /api/findings`
Returns searchable findings filtered by severity, status, or change request.

### `PATCH /api/findings/{finding_id}`
Updates finding status (`OPEN`, `ACKNOWLEDGED`, `RESOLVED`).

### `GET /api/audit`
Returns the immutable, chronological governance audit log.
