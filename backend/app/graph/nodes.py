"""
LangGraph node implementations for the Research Copilot workflow.

Workflow shape:

    plan_research -> fetch_website -> analyze_company -> assess_business
        -> quality_check --(insufficient, retries left)--> analyze_company
        quality_check --(sufficient OR retries exhausted)--> generate_report

Design principles applied across every node:
  * Never raise — failures are caught and recorded in state["node_errors"]
    plus a per-node fallback value, so one bad LLM call degrades gracefully
    instead of crashing the whole session (failure handling + recoverability).
  * Each node returns only the keys it touches (LangGraph merges dict
    updates into the shared state).
"""
from typing import Any

import requests
from bs4 import BeautifulSoup

from app.config import get_settings
from app.graph.state import ResearchState
from app.llm import LLMError, call_llm, extract_json
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


def _record_error(state: ResearchState, node: str, message: str) -> dict:
    errors = dict(state.get("node_errors", {}))
    errors[node] = message
    return {"node_errors": errors}


# ---------------------------------------------------------------------------
# Node 1: Planner
# ---------------------------------------------------------------------------
def plan_research(state: ResearchState) -> dict:
    logger.info("[%s] plan_research starting", state["session_id"])
    system = (
        "You are a research planner for a B2B sales research copilot. Given a "
        "company name, website, and the user's research objective, produce a "
        "focused research plan as a research plan JSON object with keys: "
        "'research_questions' (3-5 short strings) and 'focus_areas' (3-6 short strings)."
    )
    user = (
        f"Company: {state['company_name']}\n"
        f"Website: {state.get('website') or 'unknown'}\n"
        f"Objective: {state['objective']}"
    )
    try:
        raw = call_llm(system, user, json_mode=True)
        data = extract_json(raw)
        return {
            "research_questions": data.get("research_questions", []),
            "focus_areas": data.get("focus_areas", []),
        }
    except (LLMError, ValueError, KeyError) as exc:
        logger.warning("[%s] plan_research failed: %s", state["session_id"], exc)
        return {
            "research_questions": [f"General research on {state['company_name']}"],
            "focus_areas": ["overview", "products", "customers"],
            **_record_error(state, "plan_research", str(exc)),
        }


# ---------------------------------------------------------------------------
# Node 2: Website fetch (non-LLM data-gathering node)
# ---------------------------------------------------------------------------
def fetch_website(state: ResearchState) -> dict:
    logger.info("[%s] fetch_website starting", state["session_id"])
    website = state.get("website")
    if not website:
        return {"website_content": "", "website_fetch_error": "No website provided"}

    url = website if website.startswith("http") else f"https://{website}"
    try:
        resp = requests.get(
            url,
            timeout=settings.WEBSITE_FETCH_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (ZylabsResearchCopilot/1.0)"},
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ").split())
        text = text[: settings.WEBSITE_FETCH_MAX_CHARS]
        return {"website_content": text, "website_fetch_error": None}
    except Exception as exc:
        logger.warning("[%s] fetch_website failed: %s", state["session_id"], exc)
        return {
            "website_content": "",
            "website_fetch_error": str(exc),
            **_record_error(state, "fetch_website", str(exc)),
        }


# ---------------------------------------------------------------------------
# Node 3: Company analysis (overview, products, customers)
# ---------------------------------------------------------------------------
def analyze_company(state: ResearchState) -> dict:
    logger.info("[%s] analyze_company starting (retry=%s)", state["session_id"], state.get("retry_count", 0))
    system = (
        "You are a B2B research analyst. Using the provided website content (if any) "
        "and your general knowledge, produce a company overview JSON object with keys: "
        "'company_overview' (2-4 sentences), 'products_services' (list of strings), "
        "'target_customers' (list of strings), 'sources' (list of strings describing "
        "where the info came from, e.g. 'company website' or 'general knowledge')."
    )
    feedback = state.get("quality_feedback")
    user = (
        f"Company: {state['company_name']}\n"
        f"Research questions: {state.get('research_questions')}\n"
        f"Website content (may be empty): {state.get('website_content', '')[:4000]}\n"
    )
    if feedback:
        user += f"\nPrevious attempt was flagged as insufficient. Feedback to address: {feedback}\n"

    try:
        raw = call_llm(system, user, json_mode=True)
        data = extract_json(raw)
        return {
            "company_overview": data.get("company_overview", ""),
            "products_services": data.get("products_services", []),
            "target_customers": data.get("target_customers", []),
            "research_sources": data.get("sources", []),
        }
    except (LLMError, ValueError, KeyError) as exc:
        logger.warning("[%s] analyze_company failed: %s", state["session_id"], exc)
        return {
            "company_overview": f"Unable to generate overview for {state['company_name']} due to a research error.",
            "products_services": [],
            "target_customers": [],
            "research_sources": [],
            **_record_error(state, "analyze_company", str(exc)),
        }


# ---------------------------------------------------------------------------
# Node 4: Business signal / risk analysis
# ---------------------------------------------------------------------------
def assess_business(state: ResearchState) -> dict:
    logger.info("[%s] assess_business starting", state["session_id"])
    system = (
        "You are a business analyst supporting sales preparation. Given the company "
        "overview and products/customers already researched, identify business signals "
        "JSON object with keys: 'business_signals' (list of strings — e.g. growth "
        "indicators, hiring, funding, news) and 'risks_challenges' (list of strings)."
    )
    user = (
        f"Company overview: {state.get('company_overview')}\n"
        f"Products/services: {state.get('products_services')}\n"
        f"Target customers: {state.get('target_customers')}\n"
        f"Website content excerpt: {state.get('website_content', '')[:3000]}\n"
    )
    try:
        raw = call_llm(system, user, json_mode=True)
        data = extract_json(raw)
        return {
            "business_signals": data.get("business_signals", []),
            "risks_challenges": data.get("risks_challenges", []),
        }
    except (LLMError, ValueError, KeyError) as exc:
        logger.warning("[%s] assess_business failed: %s", state["session_id"], exc)
        return {
            "business_signals": [],
            "risks_challenges": ["Unable to assess risks due to a research error."],
            **_record_error(state, "assess_business", str(exc)),
        }


# ---------------------------------------------------------------------------
# Node 5: Quality check (drives conditional routing)
# ---------------------------------------------------------------------------
def quality_check(state: ResearchState) -> dict:
    logger.info("[%s] quality_check starting", state["session_id"])
    system = (
        "You are a strict quality reviewer for a sales research report. Judge whether "
        "the research so far is specific and useful enough to brief a salesperson. "
        "Respond as quality assessment JSON object with keys: 'is_sufficient' (boolean), "
        "'confidence' (0-1 float), 'feedback' (1-2 sentences on what's missing, or "
        "'looks good' if sufficient)."
    )
    user = (
        f"Company overview: {state.get('company_overview')}\n"
        f"Products/services: {state.get('products_services')}\n"
        f"Business signals: {state.get('business_signals')}\n"
        f"Risks: {state.get('risks_challenges')}\n"
    )
    try:
        raw = call_llm(system, user, json_mode=True)
        data = extract_json(raw)
        return {
            "quality_is_sufficient": bool(data.get("is_sufficient", True)),
            "quality_confidence": float(data.get("confidence", 0.7)),
            "quality_feedback": data.get("feedback", ""),
        }
    except (LLMError, ValueError, KeyError) as exc:
        logger.warning("[%s] quality_check failed, defaulting to pass-through: %s", state["session_id"], exc)
        # Fail open: don't loop forever if the reviewer itself errors.
        return {
            "quality_is_sufficient": True,
            "quality_confidence": 0.5,
            "quality_feedback": "Quality check unavailable; proceeding with best-effort research.",
            **_record_error(state, "quality_check", str(exc)),
        }


def route_after_quality_check(state: ResearchState) -> str:
    """Conditional routing function used by the graph's conditional edge."""
    retry_count = state.get("retry_count", 0)
    if not state.get("quality_is_sufficient", True) and retry_count < settings.MAX_QUALITY_RETRIES:
        return "retry"
    return "proceed"


def increment_retry(state: ResearchState) -> dict:
    return {"retry_count": state.get("retry_count", 0) + 1}


# ---------------------------------------------------------------------------
# Node 6: Report generation
# ---------------------------------------------------------------------------
def generate_report(state: ResearchState) -> dict:
    logger.info("[%s] generate_report starting", state["session_id"])
    system = (
        "You are preparing a final sales briefing. Using all research gathered, "
        "produce discovery-prep JSON object with keys: 'discovery_questions' "
        "(4-6 strings, tailored open-ended questions a seller could ask), "
        "'outreach_strategy' (2-4 sentences), 'unknowns' (list of strings — gaps "
        "in the research that still need to be filled in by the seller)."
    )
    user = (
        f"Objective: {state['objective']}\n"
        f"Company overview: {state.get('company_overview')}\n"
        f"Products/services: {state.get('products_services')}\n"
        f"Target customers: {state.get('target_customers')}\n"
        f"Business signals: {state.get('business_signals')}\n"
        f"Risks: {state.get('risks_challenges')}\n"
    )
    try:
        raw = call_llm(system, user, json_mode=True)
        data = extract_json(raw)
        discovery_questions = data.get("discovery_questions", [])
        outreach_strategy = data.get("outreach_strategy", "")
        unknowns = data.get("unknowns", [])
    except (LLMError, ValueError, KeyError) as exc:
        logger.warning("[%s] generate_report failed: %s", state["session_id"], exc)
        discovery_questions, outreach_strategy, unknowns = [], "", []
        state = {**state, **_record_error(state, "generate_report", str(exc))}

    final_report: dict[str, Any] = {
        "company_overview": state.get("company_overview", ""),
        "products_services": state.get("products_services", []),
        "target_customers": state.get("target_customers", []),
        "business_signals": state.get("business_signals", []),
        "risks_challenges": state.get("risks_challenges", []),
        "discovery_questions": discovery_questions,
        "outreach_strategy": outreach_strategy,
        "unknowns": unknowns,
        "sources": state.get("research_sources", [])
        + (["Company website"] if state.get("website_content") else []),
        "quality": {
            "confidence": state.get("quality_confidence"),
            "feedback": state.get("quality_feedback"),
            "retries": state.get("retry_count", 0),
        },
        "node_errors": state.get("node_errors", {}),
    }

    return {
        "discovery_questions": discovery_questions,
        "outreach_strategy": outreach_strategy,
        "unknowns": unknowns,
        "final_report": final_report,
    }
