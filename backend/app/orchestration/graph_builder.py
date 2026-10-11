from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
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


def build_change_assurance_graph():
    """
    Constructs the LangGraph change assurance workflow.
    Configures typed state transitions, checkpointing, and human review pause gates.
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

    # 2. Add sequential and conditional transitions
    workflow.add_edge(START, "change_understanding")
    workflow.add_edge("change_understanding", "insurance_context")
    workflow.add_edge("insurance_context", "impact_analysis")
    workflow.add_edge("impact_analysis", "test_planning")
    workflow.add_edge("test_planning", "test_execution")
    workflow.add_edge("test_execution", "readiness_assessment")
    workflow.add_edge("readiness_assessment", "human_review_gate")
    workflow.add_edge("human_review_gate", END)

    # 3. Checkpointing for durability & resumability
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    return app


change_assurance_app = build_change_assurance_graph()
