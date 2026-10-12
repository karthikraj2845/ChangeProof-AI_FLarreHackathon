# ChangeProof AI

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-blue.svg)](https://www.typescriptlang.org/)
[![Tests Passing](https://img.shields.io/badge/tests-56%20passed-brightgreen.svg)]()

> **Every Insurance Change. Traced, Tested, Verified.**  
> *A Production-Inspired, Insurance-Native Agentic AI Platform for Flarre.AI Innovation Challenge 2026*

---

## 1. Executive Summary & Problem Statement

Property and casualty (P&C) insurance platforms contain deeply interconnected underwriting rules, rating logic, product configurations, policy issuance workflows, and regulatory filings. 

A seemingly small modification to a business rule—such as relaxing an eligibility condition—can trigger unintended regressions across rating services or violate state insurance filings. 

**ChangeProof AI** establishes a continuous, version-aware evidence chain from the original natural-language business change request, through graph-derived dependency reachability, deterministic regression testing, human governance gates, and post-deployment runtime transaction verification (**IntentGuard**).

### Core Architectural Principle
**LangGraph orchestrates the workflow; it does NOT replace or hallucinate core insurance logic.**
- **AI Agents** interpret user requests, retrieve context, explain graph paths, and synthesize exploratory test proposals.
- **Deterministic Engines** evaluate rules, traverse dependency graphs, execute tests, and enforce release blockers.
- **Zero Hallucination Gate:** An LLM agent cannot override a deterministic regression blocker.

---

## 2. Key Capabilities & Features

1. **Change Understanding Agent:** Converts natural-language rule changes into validated structured operations (`REMOVE_CONDITION`, `MODIFY_THRESHOLD`).
2. **Insurance Context Agent:** Retrieves grounded requirements, product configurations, and version definitions from the database.
3. **RuleRipple Impact Agent & Graph:** NetworkX-powered dependency graph computing downstream blast radius and explainable impact scores based on reach, criticality, proximity, and uncertainty.
4. **Test Planning Agent:** Discovers linked test suites and synthesizes candidate edge-case proposals (clearly labeled as unvalidated until executed).
5. **Deterministic Rule Engine:** Safe, schema-based condition evaluator (zero arbitrary Python `eval`).
6. **Side-by-Side Regression Matrix:** Compares baseline vs proposed rule outcomes across 8 comprehensive underwriting scenarios.
7. **Seeded Defect Detection:** Flawlessly detects the deliberate defect in `TEST-SD-002` (unsupported jurisdiction driver receiving unauthorized discount).
8. **Deterministic Release Readiness Policy:** Strictly enforces `BLOCKED` status when regressions exist, preventing unverified deployment.
9. **Human Governance Gate:** LangGraph-persisted interruption allowing underwriters to review evidence, record justifications, and formally approve or reject releases.
10. **IntentGuard Runtime Verifier:** Evaluates simulated or live production transactions against the explicitly approved reference version and creates traceable `Findings` on behavioral deviations.
11. **Continuous Audit Trail:** Immutable, cryptographically ordered event log tracking all agent actions and human decisions.
12. **Offline-Capable / Zero-Credential Fallback:** Runs 100% locally with deterministic heuristic reasoning if an OpenAI API key is not supplied.

---

## 3. Technology Stack

- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, NetworkX, LangGraph, LangChain Core, Pytest, HTTPX, SQLite (local default) / PostgreSQL support.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, React Flow (`@xyflow/react`), Recharts, Lucide React, Axios.
- **DevOps & Containers:** Docker, Docker Compose, Nginx.

---

## 4. Quick Start & Setup Instructions

### Prerequisites
- Python 3.11 or higher
- Node.js v18+ and npm
- Git

### 1. Clone & Set Up Backend

```bash
# In project root
python -m venv venv

# Windows activate:
.\venv\Scripts\activate
# Linux/macOS activate:
# source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Configure environment variables (optional: works offline out of the box!)
cp backend/.env.example backend/.env

# Seed the motor insurance demonstration scenario
cd backend
python -m app.db.seed
```

### 2. Start the Backend API Server

```bash
# From within the backend directory (with venv activated):
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### 3. Set Up & Start the Frontend

```bash
# In a separate terminal, navigate to the frontend directory:
cd frontend
npm install
npm run dev
```
- Frontend UI: `http://localhost:5173`

---

## 5. Docker Compose Startup (Alternative)

To run the full stack in isolated containers:

```bash
docker-compose up --build
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`

---

## 6. Running the Automated Test Suite

ChangeProof AI includes comprehensive unit, integration, and end-to-end acceptance tests:

```bash
cd backend
pytest -v
```

### Actual Test Execution Results
```text
============================= test session starts =============================
platform win32 -- Python 3.13.9, pytest-9.1.1, pluggy-1.6.0
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1, langsmith-0.14.7, asyncio-1.4.0

tests/test_api_endpoints.py::test_health_check_endpoint PASSED           [  3%]
tests/test_api_endpoints.py::test_dashboard_summary_endpoint PASSED      [  6%]
tests/test_api_endpoints.py::test_rules_and_versions_endpoints PASSED    [ 10%]
tests/test_api_endpoints.py::test_dependency_graph_endpoint PASSED       [ 13%]
tests/test_api_endpoints.py::test_intentguard_simulation_endpoint PASSED [ 17%]
tests/test_change_parser.py::test_valid_safe_driver_discount_change PASSED [ 20%]
tests/test_change_parser.py::test_modify_driver_risk_score_threshold PASSED [ 24%]
tests/test_change_parser.py::test_empty_request_handling PASSED          [ 27%]
tests/test_change_parser.py::test_vague_request_handling PASSED          [ 31%]
tests/test_change_parser.py::test_unsupported_operation_handling PASSED  [ 34%]
tests/test_change_parser.py::test_contradictory_request_handling PASSED  [ 37%]
tests/test_change_parser.py::test_pydantic_schema_validation_untrusted_input PASSED [ 41%]
tests/test_e2e_acceptance.py::test_mandatory_end_to_end_acceptance PASSED [ 44%]
tests/test_governance_snapshots.py::test_immutable_snapshot_creation_and_integrity PASSED [ 48%]
tests/test_governance_snapshots.py::test_stale_evidence_detection_on_mutated_version PASSED [ 51%]
tests/test_governance_snapshots.py::test_tampered_snapshot_payload_detection PASSED [ 55%]
tests/test_graph_dynamic_expansion.py::test_dynamic_graph_expansion_discovers_new_tests PASSED [ 58%]
tests/test_graph_dynamic_expansion.py::test_dependency_graph_cycle_handling PASSED [ 62%]
tests/test_graph_service.py::test_graph_loading_and_traversal PASSED     [ 65%]
tests/test_graph_service.py::test_impact_score_calculation PASSED        [ 68%]
tests/test_intent_guard.py::test_intent_guard_detects_deviation_and_creates_finding PASSED [ 72%]
tests/test_langgraph_workflow.py::test_langgraph_workflow_execution_and_resumption PASSED [ 75%]
tests/test_langgraph_workflow.py::test_langgraph_revision_request_routing PASSED [ 79%]
tests/test_readiness_policy.py::test_readiness_policy_blocks_on_regression PASSED [ 82%]
tests/test_readiness_policy.py::test_readiness_policy_passes_clean_release PASSED [ 86%]
tests/test_regression_runner.py::test_regression_test_runner_detects_seeded_defect PASSED [ 89%]
tests/test_rule_engine.py::test_rule_condition_operators PASSED          [ 93%]
tests/test_rule_engine.py::test_rule_evaluation_baseline_success PASSED  [ 96%]
tests/test_rule_engine.py::test_rule_evaluation_baseline_rejection_unsupported_state PASSED [100%]

============================= 29 passed in 3.27s ==============================
```

---

## 7. The Core Demonstration Scenario

1. **Baseline Rule (`v1.0 - APPROVED`):**
   - 10% safe driver discount granted ONLY IF:
     1. Jurisdiction in `['CA', 'TX', 'FL', 'NY', 'IL']`
     2. Driver telematics risk score `<= 25`
     3. Vehicle category in `['SEDAN', 'SUV', 'COUPE', 'MINIVAN']`
     4. Policy is active (`True`)
2. **Proposed Change (`CR-2026-001`):**
   - User request: *"Remove the jurisdiction restriction from the safe-driver discount eligibility rule."*
   - Candidate `v1.1-proposed` accidentally deletes state validation.
3. **Seeded Defect:**
   - In `TEST-SD-002`, a driver from Nevada (`NV`) with risk score 15 receives 0% in baseline v1.0, but incorrectly qualifies for 10% in proposed v1.1.
4. **Automated Protection:**
   - Test runner flags behavioral regression in `TEST-SD-002`.
   - Readiness policy locks release as `BLOCKED`.
   - Underwriter rejects candidate version.
   - IntentGuard detects runtime deviation on live NV quote request and generates a traceable finding.

---

## 8. 3-Minute Hackathon Demo Guide

Follow the narrative in [`docs/demo-script.md`](./docs/demo-script.md):
- **0:00–0:30 (Problem):** Introduce the safe-driver discount rule and accidental jurisdiction deletion.
- **0:30–1:00 (Agentic Workflow & RuleRipple):** Show LangGraph node execution and interactive NetworkX graph paths.
- **1:00–1:40 (Testing):** Inspect side-by-side matrix showing `TEST-SD-002` regression.
- **1:40–2:15 (Readiness):** Show deterministic `BLOCKED` verdict and human review rejection.
- **2:15–2:45 (IntentGuard):** Simulate Nevada transaction and observe `DEVIATION DETECTED` alert with linked finding.
- **2:45–3:00 (Value):** Summarize the end-to-end evidence chain.

---

## 9. Repository Structure

```text
changeproof-ai/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI REST endpoints
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── db/              # Database session & seed script
│   │   ├── agents/          # Agent prompts & heuristics
│   │   ├── orchestration/   # LangGraph state, nodes & runner
│   │   ├── rules/           # Deterministic rule engine
│   │   ├── graph/           # NetworkX graph service
│   │   ├── testing/         # Deterministic regression runner
│   │   ├── verification/    # IntentGuard runtime verifier
│   │   ├── services/        # Readiness & findings services
│   │   ├── ai/              # Provider abstraction (OpenAI / Heuristic)
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/               # Pytest suite (16 tests)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── api/             # Typed Axios client
│   │   ├── components/      # Badges, MetricCards, Navbar, CustomNode
│   │   ├── features/        # Dashboard, Changes, Workflow, Graph, Testing, Readiness, IntentGuard, Findings
│   │   ├── layouts/         # AppLayout
│   │   ├── types/           # TypeScript definitions
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docs/
│   ├── architecture.md      # System architecture specification
│   ├── api.md               # Complete REST API documentation
│   ├── evaluation.md        # Synthetic benchmark evaluation report
│   └── demo-script.md       # 3-minute hackathon demo script
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

## 10. License & Credits

Built for the **Flarre.AI Innovation Challenge 2026**.
Developed with insurance-native engineering principles, deterministic verification, and agentic AI.
