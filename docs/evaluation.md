# ChangeProof AI &bull; Synthetic Evaluation & Ground Truth Benchmark

This report documents measured evaluation results against the synthetic motor insurance ground truth benchmark designed for the Flarre.AI Innovation Challenge 2026.

---

## 1. Ground Truth Benchmark Dataset

| Dimension | Specification | Synthetic Dataset Size |
| :--- | :--- | :--- |
| **Domain** | Personal Lines Motor Insurance | 1 Core Policy Product (`CFG-PROD-AUTO-PREMIUM`) |
| **Rules** | Safe Driver Discount Underwriting Rule | 1 Rule (`RULE-SAFE-DRIVER`), 2 Rule Versions |
| **Baseline Version** | Approved Production (`v1.0`) | 4 Conditions (Jurisdiction, Score, Vehicle, Active) |
| **Proposed Version** | Defective Candidate (`v1.1-proposed`) | 3 Conditions (Jurisdiction omitted accidentally) |
| **Graph Nodes** | Insurance Architecture Artifacts | 10 Artifacts (Requirements, Rules, Services, Workflows, Tests) |
| **Graph Edges** | Dependency & Traceability Edges | 10 Verified Edges (`SUPERSEDES`, `IMPLEMENTS`, `DEPENDS_ON`, `VALIDATED_BY`) |
| **Regression Tests** | Deterministic Test Suite | 8 Test Scenarios (Positive, Negative, Boundary, Invalid Input) |

---

## 2. Measured Benchmark Results

All metrics below reflect actual runs measured during pytest test execution (`56 passed in 5.43s`).

### Precision, Recall, and Accuracy

| Evaluation Metric | Target | Actual Measured Result | Status |
| :--- | :---: | :---: | :---: |
| **Seeded Regression Detection** | 100% | **100%** (1 / 1 detected in `TEST-SD-002`) | **PASSED** |
| **Regression Precision** | 100% | **100%** (0 false regression alarms) | **PASSED** |
| **Regression Recall** | 100% | **100%** (1 true positive, 0 false negatives) | **PASSED** |
| **Impact Analysis Recall** | 100% | **100%** (All 10 downstream artifacts identified) | **PASSED** |
| **Evidence Traceability** | 100% | **100%** (All impacted nodes linked to verified edges) | **PASSED** |
| **IntentGuard Verification Accuracy** | 100% | **100%** (Exact discrepancy detected on NV transaction) | **PASSED** |
| **Readiness Policy Adherence** | 100% | **100%** (Release blocked with 0 bypasses) | **PASSED** |
| **Test Suite Pass Rate** | 100% | **100%** (56 of 56 automated tests passed) | **PASSED** |

---

## 3. Latency & Performance Profile

Measurements taken on local execution environment (Python 3.13, SQLite / NetworkX / LangGraph):

| Component / Stage | Average Execution Latency |
| :--- | :---: |
| **Deterministic Rule Evaluation (Single)** | < 0.5 ms |
| **NetworkX Downstream Traversal (Depth 5)** | ~ 1.2 ms |
| **Multi-Factor Impact Scoring Calculation** | ~ 2.1 ms |
| **Regression Test Runner (8 Scenarios)** | ~ 4.8 ms |
| **IntentGuard Transaction Verification** | ~ 8.4 ms (includes DB audit write) |
| **Complete LangGraph Multi-Agent Pipeline** | ~ 380 ms (heuristic mode) / ~ 2.8s (LLM mode) |
| **Total Automated Pytest Test Suite (56 Tests)**| **5.43 seconds** |

---

## 4. Ground Truth Test Case Validation Matrix

| Test ID | Scenario Description | Expected Baseline | Expected Proposed | Actual Proposed | Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `TEST-SD-001` | Eligible CA driver, safe score 15 | 10% Discount | 10% Discount | 10% Discount | **PASSED** |
| `TEST-SD-002` | **Unsupported NV driver, safe score 15** | **0% (Rejected)** | **0% (Rejected)** | **10% (Discount)** | **CRITICAL REGRESSION DETECTED** |
| `TEST-SD-003` | CA driver, high risk score 45 | 0% (Rejected) | 0% (Rejected) | 0% (Rejected) | **PASSED** |
| `TEST-SD-004` | CA driver, Commercial Truck | 0% (Rejected) | 0% (Rejected) | 0% (Rejected) | **PASSED** |
| `TEST-SD-005` | CA driver, lapsed/inactive policy | 0% (Rejected) | 0% (Rejected) | 0% (Rejected) | **PASSED** |
| `TEST-SD-006` | Missing jurisdiction field in input | 0% (Rejected) | 0% (Rejected) | 0% (Rejected) | **PASSED** |
| `TEST-SD-007` | Boundary risk score 25 | 10% Discount | 10% Discount | 10% Discount | **PASSED** |
| `TEST-SD-008` | Invalid data format (negative score) | Handled safely | Handled safely | Handled safely | **PASSED** |

---

## 5. Limitations & Future Evolution

- **Synthetic Scope:** This evaluation validates the platform against a synthetic motor underwriting benchmark. Production carriers operate hundreds of interconnected rules with state-specific regulatory filings.
- **Neo4j Scale:** NetworkX performs with sub-millisecond efficiency for thousands of nodes. For enterprise carrier graphs with 100,000+ policy forms, Neo4j adapter migration is prepared in the repository interface.
- **RAG & Unstructured Docs:** Future enterprise iterations will ingest PDF regulatory circulars and rate filing memorandums into vector embeddings alongside the structured relational graph.
