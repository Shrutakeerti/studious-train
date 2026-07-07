"""
Assembles the LangGraph StateGraph for the research workflow and exposes a
single `run_workflow` entrypoint that the FastAPI layer calls. Execution is
streamed node-by-node so the caller can persist progress after every step
(powers the Workflow Progress UI) rather than only seeing a final result.
"""
from collections.abc import Callable, Iterator

from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    analyze_company,
    assess_business,
    fetch_website,
    generate_report,
    increment_retry,
    plan_research,
    quality_check,
    route_after_quality_check,
)
from app.graph.state import ResearchState
from app.logging_config import get_logger

logger = get_logger(__name__)


def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("plan_research", plan_research)
    graph.add_node("fetch_website", fetch_website)
    graph.add_node("analyze_company", analyze_company)
    graph.add_node("assess_business", assess_business)
    graph.add_node("quality_check", quality_check)
    graph.add_node("increment_retry", increment_retry)
    graph.add_node("generate_report", generate_report)

    graph.set_entry_point("plan_research")
    graph.add_edge("plan_research", "fetch_website")
    graph.add_edge("fetch_website", "analyze_company")
    graph.add_edge("analyze_company", "assess_business")
    graph.add_edge("assess_business", "quality_check")

    # Conditional routing: loop back for another research pass if the
    # quality reviewer flags the output as insufficient, otherwise proceed.
    graph.add_conditional_edges(
        "quality_check",
        route_after_quality_check,
        {"retry": "increment_retry", "proceed": "generate_report"},
    )
    graph.add_edge("increment_retry", "analyze_company")
    graph.add_edge("generate_report", END)

    return graph.compile()


_compiled_graph = build_graph()


def run_workflow_streaming(
    initial_state: ResearchState,
    on_step: Callable[[str, dict], None],
) -> ResearchState:
    """
    Runs the compiled graph, invoking on_step(node_name, node_output) after
    every node completes so the caller can persist progress incrementally.
    Returns the final accumulated state.
    """
    final_state: dict = dict(initial_state)

    for chunk in _compiled_graph.stream(initial_state, stream_mode="updates"):
        # chunk looks like {"node_name": {...partial state updates...}}
        for node_name, updates in chunk.items():
            logger.info("Node '%s' completed", node_name)
            final_state.update(updates)
            on_step(node_name, updates)

    return final_state  # type: ignore[return-value]
