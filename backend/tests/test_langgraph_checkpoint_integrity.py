"""
Priority 3: LangGraph Checkpoint Integrity Tests
Verifies genuine LangGraph pause/resume by inspecting checkpoint state,
thread ID, pending interruption, and resumed state.
Tests duplicate decisions, invalid actions, and concurrent workflow isolation.
Uses MemorySaver for test isolation.
"""
import pytest
import uuid
from langgraph.checkpoint.memory import MemorySaver
from app.orchestration.graph_builder import build_change_assurance_graph
from app.orchestration.state import WorkflowState
from app.db.session import SessionLocal
from app.models.workflow import WorkflowRun
from app.models.audit import AuditEvent
from app.orchestration.runner import WorkflowRunner


def _build_isolated_graph():
    """Build a graph with MemorySaver for test isolation."""
    checkpointer = MemorySaver()
    app = build_change_assurance_graph(checkpointer=checkpointer)
    return app, checkpointer


def _make_initial_state(thread_id: str) -> WorkflowState:
    """Create a minimal initial state for testing."""
    return {
        "workflow_id": thread_id,
        "change_request_id": "CR-2026-001",
        "user_request": "Remove the jurisdiction restriction from the safe-driver discount eligibility rule.",
        "target_rule_id": "RULE-SAFE-DRIVER",
        "baseline_version_id": "RULE-SAFE-DRIVER-v1.0",
        "proposed_version_id": "RULE-SAFE-DRIVER-v1.1-proposed",
        "current_stage": "start",
        "status": "RUNNING",
        "errors": [],
        "warnings": [],
        "execution_metadata": {},
    }


class TestLangGraphCheckpointIntegrity:
    """Verify genuine LangGraph pause and resume through checkpoint inspection."""

    def test_graph_pauses_at_human_review_gate_with_checkpoint(self):
        """
        Invoke graph → verify get_state() shows pending human_review_gate node
        → graph is genuinely interrupted, not just a status update.
        """
        app, checkpointer = _build_isolated_graph()
        thread_id = f"WF-CHK-{uuid.uuid4().hex[:8].upper()}"
        config = {"configurable": {"thread_id": thread_id}}
        initial_state = _make_initial_state(thread_id)

        # Invoke — should pause at human_review_gate
        paused_state = app.invoke(initial_state, config=config)

        # Verify the graph is genuinely paused (not at END)
        graph_state = app.get_state(config)
        assert graph_state is not None, "Checkpoint state must exist after invoke"

        # The pending 'next' should be the human_review_gate node
        pending_next = graph_state.next
        assert "human_review_gate" in pending_next, (
            f"Expected graph to be paused before 'human_review_gate', got next={pending_next}"
        )

        # Verify the thread_id in the config matches
        assert graph_state.config["configurable"]["thread_id"] == thread_id

        # Verify state values are populated by the prior nodes
        values = graph_state.values
        assert values.get("workflow_id") == thread_id
        assert values.get("target_rule_id") == "RULE-SAFE-DRIVER"
        assert len(values.get("test_results", [])) > 0, "Tests must have run before pause"
        assert values.get("readiness_result") is not None, "Readiness must be computed before pause"
        assert values.get("snapshot_id") is not None, "Snapshot must be created before pause"

    def test_graph_resumes_through_human_review_gate_to_end(self):
        """
        Invoke → verify pause → update_state with decision → invoke(None) → verify final state at END.
        """
        app, checkpointer = _build_isolated_graph()
        thread_id = f"WF-RSM-{uuid.uuid4().hex[:8].upper()}"
        config = {"configurable": {"thread_id": thread_id}}
        initial_state = _make_initial_state(thread_id)

        # Phase 1: Invoke to pause
        app.invoke(initial_state, config=config)
        state_before_resume = app.get_state(config)
        assert "human_review_gate" in state_before_resume.next

        # Phase 2: Inject human decision via update_state
        decision = {
            "reviewer": "Test Reviewer",
            "action": "REJECT",
            "justification": "Test rejection for checkpoint verification",
            "timestamp": "2026-10-12T10:00:00Z",
        }
        app.update_state(
            config,
            {"human_review_decision": decision},
            as_node="readiness_assessment",
        )

        # Phase 3: Resume execution
        resumed_state = app.invoke(None, config=config)

        # Phase 4: Verify final state
        final_graph_state = app.get_state(config)
        assert final_graph_state.next == (), (
            f"Graph should be at END after resume, but next={final_graph_state.next}"
        )

        # Verify the decision was properly propagated through the human_review_gate node
        final_values = final_graph_state.values
        assert final_values.get("human_review_decision") is not None
        assert final_values["human_review_decision"]["reviewer"] == "Test Reviewer"
        assert final_values["human_review_decision"]["action"] == "REJECT"

    def test_concurrent_workflow_isolation(self):
        """
        Two different thread_ids must not interfere — each has independent checkpoint state.
        """
        app, checkpointer = _build_isolated_graph()

        thread_a = f"WF-ISO-A-{uuid.uuid4().hex[:8].upper()}"
        thread_b = f"WF-ISO-B-{uuid.uuid4().hex[:8].upper()}"
        config_a = {"configurable": {"thread_id": thread_a}}
        config_b = {"configurable": {"thread_id": thread_b}}

        state_a = _make_initial_state(thread_a)
        state_b = _make_initial_state(thread_b)

        # Invoke both
        app.invoke(state_a, config=config_a)
        app.invoke(state_b, config=config_b)

        # Both should be independently paused
        graph_a = app.get_state(config_a)
        graph_b = app.get_state(config_b)
        assert "human_review_gate" in graph_a.next
        assert "human_review_gate" in graph_b.next

        # Resume only A
        app.update_state(
            config_a,
            {"human_review_decision": {
                "reviewer": "Reviewer A",
                "action": "REJECT",
                "justification": "Reject A",
                "timestamp": "2026-10-12T10:00:00Z",
            }},
            as_node="readiness_assessment",
        )
        app.invoke(None, config=config_a)

        # A should be at END, B should still be paused
        final_a = app.get_state(config_a)
        still_paused_b = app.get_state(config_b)

        assert final_a.next == (), f"A should be at END, got {final_a.next}"
        assert "human_review_gate" in still_paused_b.next, (
            f"B should still be paused, got {still_paused_b.next}"
        )

        # Verify workflow_ids are different in the two checkpoint states
        assert final_a.values["workflow_id"] == thread_a
        assert still_paused_b.values["workflow_id"] == thread_b


class TestWorkflowRunnerGovernance:
    """
    Test governance enforcement in the WorkflowRunner: duplicate decisions,
    invalid actions, and blocker enforcement via the actual runner (not just graph).
    """

    def test_invalid_action_rejected(self):
        """
        An invalid action like 'DEPLOY' must raise a clear ValueError.
        """
        db = SessionLocal()
        try:
            state = WorkflowRunner.start_change_assurance(
                db=db,
                change_request_id="CR-2026-001",
                user_request="Remove the jurisdiction restriction from the safe-driver discount eligibility rule.",
            )
            wf_id = state["workflow_id"]

            with pytest.raises(ValueError, match="Invalid review action"):
                WorkflowRunner.resume_with_review(
                    db=db,
                    workflow_id=wf_id,
                    reviewer="Rogue Actor",
                    action="DEPLOY",
                    justification="Trying to deploy directly.",
                )
        finally:
            db.close()

    def test_duplicate_approval_after_reject_is_prevented(self):
        """
        After a workflow is rejected, attempting to approve it again must fail.
        """
        db = SessionLocal()
        try:
            state = WorkflowRunner.start_change_assurance(
                db=db,
                change_request_id="CR-2026-001",
                user_request="Remove the jurisdiction restriction from the safe-driver discount eligibility rule.",
            )
            wf_id = state["workflow_id"]

            # First: valid REJECT
            WorkflowRunner.resume_with_review(
                db=db,
                workflow_id=wf_id,
                reviewer="Reviewer",
                action="REJECT",
                justification="Rejecting for test.",
            )

            # Second: duplicate submission must fail
            with pytest.raises(ValueError, match="Cannot submit duplicate review"):
                WorkflowRunner.resume_with_review(
                    db=db,
                    workflow_id=wf_id,
                    reviewer="Another Reviewer",
                    action="APPROVE",
                    justification="Trying to approve after rejection.",
                )
        finally:
            db.close()

    def test_blocker_override_creates_audit_event(self):
        """
        Attempting to APPROVE a BLOCKED workflow must create an audit denial event.
        """
        db = SessionLocal()
        try:
            state = WorkflowRunner.start_change_assurance(
                db=db,
                change_request_id="CR-2026-001",
                user_request="Remove the jurisdiction restriction from the safe-driver discount eligibility rule.",
            )
            wf_id = state["workflow_id"]

            # Count denial audit events before
            before_count = db.query(AuditEvent).filter(
                AuditEvent.event_type == "APPROVAL_ATTEMPT_DENIED_REGRESSION_BLOCK",
                AuditEvent.entity_id == wf_id,
            ).count()

            # Attempt override (must fail)
            with pytest.raises(ValueError, match="GOVERNANCE VIOLATION"):
                WorkflowRunner.resume_with_review(
                    db=db,
                    workflow_id=wf_id,
                    reviewer="Override Manager",
                    action="APPROVE",
                    justification="Force approval.",
                    snapshot_id=state["snapshot_id"],
                    snapshot_hash=state["snapshot_hash"],
                )

            # Count denial audit events after — must be one more
            after_count = db.query(AuditEvent).filter(
                AuditEvent.event_type == "APPROVAL_ATTEMPT_DENIED_REGRESSION_BLOCK",
                AuditEvent.entity_id == wf_id,
            ).count()
            assert after_count == before_count + 1, "Denial audit event must be recorded"
        finally:
            db.close()

    def test_durable_checkpoint_recovery_across_checkpointer_recreation(self, tmp_path):
        """
        Priority 4: Inspect persistent SqliteSaver.
        Pause at human review, simulate application/checkpointer recreation by opening
        a brand-new SqliteSaver on the same SQLite file, verify thread state is recovered,
        and resume workflow through human review gate to END.
        """
        import sqlite3
        from langgraph.checkpoint.sqlite import SqliteSaver

        db_file = str(tmp_path / "test_durable_checkpoints.db")
        thread_id = f"WF-DURABLE-{uuid.uuid4().hex[:8].upper()}"
        config = {"configurable": {"thread_id": thread_id}}
        initial_state = _make_initial_state(thread_id)

        # 1. Initialize First Checkpointer & Graph Instance
        conn1 = sqlite3.connect(db_file, check_same_thread=False)
        saver1 = SqliteSaver(conn1)
        saver1.setup()
        app1 = build_change_assurance_graph(checkpointer=saver1)

        # Invoke to pause at human_review_gate
        app1.invoke(initial_state, config=config)

        # Verify state is paused before human review gate
        paused_state1 = app1.get_state(config)
        assert "human_review_gate" in paused_state1.next
        assert paused_state1.values.get("workflow_id") == thread_id

        # Close first connection to simulate process shutdown
        conn1.close()

        # 2. Simulate Application Restart: Open brand new SqliteSaver on the same DB file
        conn2 = sqlite3.connect(db_file, check_same_thread=False)
        saver2 = SqliteSaver(conn2)
        saver2.setup()
        app2 = build_change_assurance_graph(checkpointer=saver2)

        # Verify state is recovered from persistent disk
        recovered_state = app2.get_state(config)
        assert recovered_state is not None, "Persistent checkpoint must be recoverable after restart"
        assert "human_review_gate" in recovered_state.next
        assert recovered_state.values.get("workflow_id") == thread_id
        assert len(recovered_state.values.get("test_results", [])) > 0

        # Inject decision and resume on the recreated graph instance
        decision = {
            "reviewer": "Disaster Recovery Auditor",
            "action": "REJECT",
            "justification": "Verified persistent resumption",
            "timestamp": "2026-10-12T12:00:00Z",
        }
        app2.update_state(
            config,
            {"human_review_decision": decision},
            as_node="readiness_assessment",
        )
        resumed = app2.invoke(None, config=config)

        # Verify resumed execution reached END
        final_state = app2.get_state(config)
        assert final_state.next == (), f"Expected END, got {final_state.next}"
        assert final_state.values["human_review_decision"]["reviewer"] == "Disaster Recovery Auditor"

        conn2.close()
