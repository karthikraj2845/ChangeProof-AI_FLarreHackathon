# ChangeProof AI &bull; 3-Minute Hackathon Demo Script

**Theme:** Every Insurance Change. Traced, Tested, Verified.  
**Demonstration Scenario:** Seeded Motor Insurance Safe-Driver Discount Defect.

---

### **0:00 – 0:30 &bull; The Problem: An Invisible Underwriting Defect**
- **Action:** Open Dashboard (`http://localhost:5173/`). Point to the hero section.
- **Presenter:**
  > *"Property and casualty insurance systems contain deeply interconnected underwriting rules, rating logic, and state filings. In this demo, an underwriting analyst submits a change request: 'Remove the jurisdiction restriction from the safe-driver discount eligibility rule.'*  
  > *In production baseline v1.0, a 10% discount is restricted strictly to approved states: CA, TX, FL, NY, IL. In candidate v1.1, the developer accidentally removed the state validation check entirely. Without automated change assurance, this defect slips into production, causing unfiled regulatory rate violations. Let's see how ChangeProof AI prevents this."*

---

### **0:30 – 1:00 &bull; Agentic Orchestration & RuleRipple Impact**
- **Action:** Click **"Launch Seeded 3-Minute Demo"** or navigate to **"Agent Workflow"**.
- **Presenter:**
  > *"Here, our LangGraph multi-agent pipeline immediately executes. Stage 1, the Change Understanding Agent, parses the request into a structured JSON operation: `REMOVE_CONDITION` on field `jurisdiction`.*  
  > *Stage 2, the Insurance Context Agent, retrieves the approved baseline v1.0 and candidate v1.1 definitions.*  
  > *Now, switch to the RuleRipple tab: RuleRipple traverses our NetworkX insurance dependency graph. Notice how it traces the change from the rule through the business requirement `REQ-AUTO-DISC-001`, down to the Eligibility Service, Rating Engine, and Policy Workflow. Every node has an explainable impact score derived from blast radius reach, criticality, and proximity."*

---

### **1:00 – 1:40 &bull; Deterministic Regression Testing**
- **Action:** Click **"Regression Tests"** tab.
- **Presenter:**
  > *"Now we move to deterministic verification. ChangeProof AI does NOT ask an LLM whether a test passed. Instead, our deterministic rule engine executes 8 scenarios against both baseline and proposed versions side-by-side.*  
  > *Look at row 2: `TEST-SD-002`! In Nevada—an unsupported jurisdiction—the baseline correctly rejected the driver with 0% discount. But candidate v1.1 incorrectly awarded a 10% discount!*  
  > *The engine flags a Critical Behavioral Regression: `status = REGRESSION`. Notice also the unvalidated AI suggestions section, showing future exploratory scenarios."*

---

### **1:40 – 2:15 &bull; Deterministic Release Readiness & Human Governance**
- **Action:** Navigate to **"Release Readiness"** tab.
- **Presenter:**
  > *"Here is the core governance principle: AI agents cannot override insurance policy. Because a behavioral regression occurred, our deterministic readiness policy produces a hard verdict: `BLOCKED`.*  
  > *Look at the Governance Actions below: the 'Approve' button is locked. As Chief Underwriting Officer, I can review the blockers, enter my justification, and click 'Reject Change (Preserve Production Safety)'. Our workflow pauses at human review gates and records every decision into an immutable audit trail."*

---

### **2:15 – 2:45 &bull; IntentGuard Post-Deployment Runtime Verification**
- **Action:** Navigate to **"IntentGuard"** tab.
- **Presenter:**
  > *"What if a rogue commit or configuration error deployed this candidate version to a live microservice? That's why we built IntentGuard.*  
  > *Let's simulate a live quote transaction from Nevada (NV) with a clean driver score of 15. Click 'Simulate & Run IntentGuard'.*  
  > *Instantly, IntentGuard compares the deployed outcome against the approved reference version v1.0.*  
  > *Verdict: `CRITICAL DEVIATION DETECTED`. The deployed service gave a 10% discount, but approved policy dictates 0%.*  
  > *IntentGuard automatically creates a traceable finding linking the transaction back to Change Request `CR-2026-001`, Requirement `REQ-AUTO-DISC-001`, and predictive test `TEST-SD-002`."*

---

### **2:45 – 3:00 &bull; Value Proposition & Closing**
- **Action:** Click **"Findings & Audit"** tab to show the complete evidence trail.
- **Presenter:**
  > *"In under 3 minutes, ChangeProof AI turned an invisible underwriting risk into an end-to-end evidence chain: from natural language change, through dependency reach, deterministic regression, human governance, and runtime transaction guardrails.*  
  > *Every insurance change: Traced, Tested, and Verified. Thank you!"*
