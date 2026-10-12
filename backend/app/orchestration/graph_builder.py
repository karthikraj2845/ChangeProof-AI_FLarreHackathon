import os
import sqlite3
from typing import Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver
from app.config import settings
from app.orchestration.state import WorkflowState
from app.orchestration.nodes import (
    change_understanding_node,
    insurance_context_node,
    impact_analysis_node,
    test_planning_node,
    test_execution_node,
    readiness_assessment_node,
    human_review_pause_node,
)


def get_checkpointer():
    """
    Returns a persistent checkpointer.
    Uses SqliteSaver backed by a persistent file for durability across process restarts.
    Falls back to MemorySaver if file access fails.
    """
    try:
        # Determine checkpointer db path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(base_dir, "changeproof_checkpoints.db")
        conn = sqlite3.connect(db_path, check_same_thread=False)
        saver = SqliteSaver(conn)
        saver.setup()
        return saver
    except Exception as e:
        print(f"Warning: Failed to initialize SqliteSaver ({e}), falling back to MemorySaver.")
        return MemorySaver()


# Global checkpointer instance shared across workflow invocations
workflow_checkpointer = get_checkpointer()


def build_change_assurance_graph(checkpointer=None):
    """
    Constructs the LangGraph change assurance workflow.
    Configures typed state transitions, checkpointing, and real human review pause gates.
    Uses interrupt_before=['human_review_gate'] so execution pauses immediately after
    readiness assessment, and only resumes when an authorized human decision is submitted.
    """
    workflow = StateGraph(WorkflowState)

    # 1. Add specialized agent & engine nodes
    workflow.add_node("change_understanding", change_understanding_node)
    workflow.add_node("insurance_context", insurance_context_node)
    workflow.add_node("impact_analysis", impact_analysis_node)
    workflow.add_node("test_planning", test_planning_node)
    workflow.add_node("test_execution", test_execution_node)
    workflow.add_node("readiness_assessment", readiness_assessment_node)
    workflow.add_node("human_review_gate", human_review_pause_node)

    # 2. Add sequential transitions
    workflow.add_edge(START, "change_understanding")
    workflow.add_edge("change_understanding", "insurance_context")
    workflow.add_edge("insurance_context", "impact_analysis")
    workflow.add_edge("impact_analysis", "test_planning")
    workflow.add_edge("test_planning", "test_execution")
    workflow.add_edge("test_execution", "readiness_assessment")
    workflow.add_edge("readiness_assessment", "human_review_gate")
    workflow.add_edge("human_review_gate", END)

    # 3. Checkpointing and human review interruption
    active_checkpointer = checkpointer or workflow_checkpointer
    app = workflow.compile(
        checkpointer=active_checkpointer,
        interrupt_before=["human_review_gate"],
    )
    return app


change_assurance_app = build_change_assurance_graph()
