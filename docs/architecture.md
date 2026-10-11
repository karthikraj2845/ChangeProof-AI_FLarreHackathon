# ChangeProof AI &bull; System Architecture & Technical Specification

> **Tagline:** Every Insurance Change. Traced, Tested, Verified.  
> **Product Category:** Insurance-native, multi-agent AI platform for change assurance and release verification.

---

## 1. Architectural Philosophy: The Boundary Principle

A fundamental rule of ChangeProof AI is: **LangGraph orchestrates the workflow; it does NOT replace or hallucinate core insurance business logic.**

```
+-----------------------------------------------------------------------------------+
|                            AI Reasoning & Interpretation                           |
|  - Change Understanding Agent (intent extraction, operator detection)             |
|  - Insurance Context Agent (domain grounding & specification retrieval)           |
|  - Test Planning Agent (coverage gap synthesis & edge-case proposal)              |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        Authoritative Deterministic Engines                        |
|  - Deterministic Insurance Rule Engine (condition evaluation, schema validation)  |
|  - NetworkX Insurance Dependency Graph (reachability, blast radius paths)         |
|  - Deterministic Regression Runner (baseline vs proposed side-by-side)            |
|  - Deterministic Readiness Policy (hard regression blockers & human gates)        |
|  - IntentGuard Post-Deployment Verifier (expected vs observed transaction audit)  |
+-----------------------------------------------------------------------------------+
```

- **AI Agents interpret and explain:** They parse natural language, suggest candidate test cases, and explain transitive dependency paths.
- **Graph Engine calculates authoritative dependencies:** Graph traversal strictly derives from verified code, service contracts, and traceability edges.
- **Rule Engine calculates authoritative outcomes:** Zero `eval()` or unvalidated code execution. All rules are structured JSON schemas evaluated deterministically.
- **Readiness Policies determine blockers:** Hard rules prevent deployments when behavioral regressions occur.

---

## 2. Logical Architecture

```text
React + TypeScript Frontend (Vite, Tailwind, React Flow, Recharts)
                       |
                       v
         FastAPI REST API Layer (Typed Pydantic Schemas)
                       |
                       v
              Application Services
                       |
                       v
            LangGraph Multi-Agent Workflow
                       |
    +------------------+------------------+------------------+
    |                  |                  |                  |
Change Agent      Context Agent      Impact Agent       Test Agent
(Understanding)   (Retrieval)        (RuleRipple)       (Planning)
    |                  |                  |                  |
    +------------------+------------------+------------------+
                       |
                       v
          Deterministic Domain Services
    +------------------+------------------+
    |                                     |
Rule Engine                         Graph Engine
(Schema Evaluator)                  (NetworkX Adapter)
    |                                     |
    +------------------+------------------+
                       |
                       v
           Regression Test Runner
     (Side-by-side Baseline vs Proposed)
                       |
                       v
       Release Readiness Policy Engine
         (BLOCKED / NEEDS_HUMAN_REVIEW)
                       |
                       v
            Human Governance Gate
          (Approve / Reject / Recalibrate)
                       |
                       v
       IntentGuard Post-Deployment Verifier
   (Simulated Event vs Approved Reference Version)
                       |
                       v
          Traceable Findings Store
      (Linked Change, Rule, Req, Evidence)
```

---

## 3. LangGraph Orchestration & State Machine

The change assurance workflow uses a typed LangGraph `WorkflowState` persisted with checkpointing:

### Workflow State Schema
- `workflow_id`: Unique execution identifier
- `change_request_id`: Originating change proposal ID
- `user_request`: Raw natural language change text
- `target_rule_id`: Resolved rule ID (e.g., `RULE-SAFE-DRIVER`)
- `baseline_version_id`: Approved production version (`RULE-SAFE-DRIVER-v1.0`)
- `proposed_version_id`: Candidate version (`RULE-SAFE-DRIVER-v1.1-proposed`)
- `parsed_change`: Structured operation, condition field, and intent
- `domain_context`: Requirement metadata, scope, and service contracts
- `impacted_artifacts`: Downstream reachability list with blast radius scores
- `dependency_paths`: Full transitive paths from Change Request to Test Suites
- `selected_tests`: Existing regression test suite IDs
- `suggested_tests`: AI-synthesized edge cases (unvalidated proposals)
- `test_results`: Baseline and proposed outcomes side-by-side
- `coverage_gaps`: Missing mandatory scenario tags
- `readiness_result`: Deterministic policy verdict and blocker list
- `human_review_decision`: Reviewer identity, action, and justification
- `current_stage` / `status`: Lifecycle indicators

### Graph Nodes
1. `change_understanding`: Parses change request.
2. `insurance_context`: Retrieves rule, requirement, and version records.
3. `impact_analysis`: Traverses NetworkX graph for reachability and explainable scoring.
4. `test_planning`: Discovers existing tests and synthesizes candidate test cases.
5. `test_execution`: Executes regression runner deterministically.
6. `readiness_assessment`: Evaluates hard regression blockers and human review triggers.
7. `human_review_gate`: Workflow pauses here, awaiting formal governance action.

---

## 4. Multi-Factor Explainable Impact Scoring

RuleRipple calculates an explainable impact score for every artifact:

$$\text{Impact Score} = (0.35 \times \text{Reach} + 0.35 \times \text{Criticality} + 0.20 \times \text{Proximity} + 0.10 \times \text{Uncertainty}) \times 100$$

- **Reach Factor (35%):** Ratio of downstream descendants in the dependency tree.
- **Criticality Factor (35%):** Intrinsic domain criticality (Rating Service: 0.95, Eligibility Service: 0.90, Rule: 0.85, Requirement: 0.80).
- **Proximity Factor (20%):** Topological distance from the originating change.
- **Uncertainty Penalty (10%):** Weighted penalty for unverified or low-confidence edges.

---

## 5. IntentGuard Runtime Verification

Post-deployment verification detects runtime drift between deployed behavior and the explicitly approved reference version:

1. **Transaction Event Ingestion:** Receives transaction input (e.g., driver from Nevada).
2. **Approved Reference Resolution:** Queries `rule_versions` for approved baseline `RULE-SAFE-DRIVER-v1.0`.
3. **Deterministic Evaluation:** Runs rule engine against the approved version.
4. **Discrepancy Check:** Compares expected outcome (0% discount) with observed deployed outcome (10% discount).
5. **Traceable Finding Generation:** If outcomes differ, classifies as `DEVIATION` and creates a `Finding` linking:
   - Originating Change Request (`CR-2026-001`)
   - Target Rule (`RULE-SAFE-DRIVER`)
   - Requirement Specification (`REQ-AUTO-DISC-001`)
   - Predictive Regression Test (`TEST-SD-002`)
   - Observed Transaction Payload & Evidence
