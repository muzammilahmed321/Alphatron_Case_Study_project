from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.agents.checkpointer import checkpointer
from app.agents.nodes.input_processing import load_context
from app.agents.nodes.performance_analysis import analyze_performance
from app.agents.nodes.retrieval import retrieve_material
from app.agents.nodes.planning import build_revision, validate_plan
from app.agents.nodes.explanation import explain_changes
from app.agents.nodes.human_review import human_review
from app.agents.nodes.persistence import persist
from app.agents.nodes.routing import (
    route_after_load,
    route_after_analysis,
    route_after_validation,
    recommend_practice,
    on_track,
)


def build_graph():
    builder = StateGraph(AgentState)

    # Add every step as a node
    builder.add_node("load_context", load_context)
    builder.add_node("analyze_performance", analyze_performance)
    builder.add_node("retrieve_material", retrieve_material)
    builder.add_node("build_revision", build_revision)
    builder.add_node("validate_plan", validate_plan)
    builder.add_node("explain_changes", explain_changes)
    builder.add_node("human_review", human_review)
    builder.add_node("persist", persist)
    builder.add_node("recommend_practice", recommend_practice)
    builder.add_node("on_track", on_track)

    # Connect them
    builder.add_edge(START, "load_context")
    builder.add_conditional_edges("load_context", route_after_load)
    builder.add_conditional_edges(
        "analyze_performance",
        route_after_analysis,
        {
            "revise": "retrieve_material",
            "practice": "recommend_practice",
            "on_track": "on_track",
        },
    )
    builder.add_edge("retrieve_material", "build_revision")
    builder.add_edge("build_revision", "validate_plan")
    builder.add_conditional_edges(
        "validate_plan",
        route_after_validation,
        {"retry": "build_revision", "explain": "explain_changes"},
    )
    builder.add_edge("explain_changes", "human_review")
    builder.add_edge("human_review", "persist")
    builder.add_edge("persist", END)
    builder.add_edge("recommend_practice", END)
    builder.add_edge("on_track", END)

    return builder.compile(checkpointer=checkpointer)


graph = build_graph()