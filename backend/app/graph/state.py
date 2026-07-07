"""
Shared graph state.

This TypedDict is threaded through every node in the LangGraph workflow.
Each node reads what it needs and writes new keys — nothing is ever
silently dropped, which is what makes the intermediate outputs (plan,
website content, draft analysis, quality feedback...) inspectable and
persistable at every step.
"""
from typing import Any, Optional, TypedDict


class ResearchState(TypedDict, total=False):
    # --- Inputs ---
    session_id: str
    company_name: str
    website: Optional[str]
    objective: str

    # --- Planner output ---
    research_questions: list[str]
    focus_areas: list[str]

    # --- Research node output ---
    website_content: str
    website_fetch_error: Optional[str]

    company_overview: str
    products_services: list[str]
    target_customers: list[str]
    research_sources: list[str]

    # --- Analysis node output ---
    business_signals: list[str]
    risks_challenges: list[str]

    # --- Quality check output ---
    quality_is_sufficient: bool
    quality_confidence: float
    quality_feedback: str
    retry_count: int

    # --- Report generation output ---
    discovery_questions: list[str]
    outreach_strategy: str
    unknowns: list[str]
    final_report: dict[str, Any]

    # --- Failure tracking (recoverability) ---
    node_errors: dict[str, str]
