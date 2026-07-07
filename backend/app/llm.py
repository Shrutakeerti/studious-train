"""
LLM client abstraction.

Wraps the Groq API behind a single `call_llm` function so LangGraph
nodes never talk to a vendor SDK directly. If no API key is configured the
client transparently falls back to a deterministic mock responder — this
means the entire workflow (and the grading of it) works even with zero
credentials, and swapping providers later only touches this file.
"""
import json
import re

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

_client = None
if settings.llm_enabled:
    try:
        from groq import Groq

        _client = Groq(api_key=settings.GROQ_API_KEY)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to init Groq client, falling back to mock: %s", exc)
        _client = None


class LLMError(Exception):
    """Raised when the LLM call fails after fallback attempts are exhausted."""


def call_llm(system: str, user: str, json_mode: bool = False) -> str:
    """
    Calls the configured LLM and returns raw text.

    If json_mode is True, the caller expects the model to return a JSON
    object; we instruct it accordingly and the caller is responsible for
    parsing (see extract_json below) since models sometimes wrap JSON in
    prose or markdown fences.
    """
    if _client is None:
        return _mock_response(system, user, json_mode)

    try:
        instructions = system
        if json_mode:
            instructions += "\n\nRespond with ONLY valid JSON. No markdown fences, no preamble."

        resp = _client.chat.completions.create(
            model=settings.GROQ_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": user},
            ],
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        raise LLMError(str(exc)) from exc


def extract_json(raw_text: str) -> dict:
    """Best-effort extraction of a JSON object from an LLM response."""
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def _mock_response(system: str, user: str, json_mode: bool) -> str:
    """
    Deterministic offline fallback so the graph is fully runnable without
    an API key. Produces plausible, clearly-labeled placeholder content
    keyed off whatever node prompt invoked it.
    """
    logger.info("LLM_PROVIDER not configured with a live key — using mock responder")

    if not json_mode:
        return (
            "[MOCK RESPONSE - no GROQ_API_KEY configured] "
            "This is placeholder content generated offline so the workflow can run "
            "end-to-end without live credentials."
        )

    if "research plan" in system.lower() or "planner" in system.lower():
        payload = {
            "research_questions": [
                "What does the company sell and to whom?",
                "What is the company's recent business trajectory?",
                "What challenges or risks might affect a sales conversation?",
            ],
            "focus_areas": ["company overview", "products", "customers", "signals", "risks"],
        }
    elif "overview" in system.lower() or "products" in system.lower():
        payload = {
            "company_overview": "[MOCK] A company operating in its stated industry, inferred from the provided name/website.",
            "products_services": ["[MOCK] Primary product line", "[MOCK] Secondary service offering"],
            "target_customers": ["[MOCK] Mid-market B2B buyers"],
            "sources": ["[MOCK] Company website (offline placeholder)"],
        }
    elif "business signals" in system.lower() or "risks" in system.lower():
        payload = {
            "business_signals": ["[MOCK] No live signals — configure GROQ_API_KEY for real analysis"],
            "risks_challenges": ["[MOCK] Unable to assess real risk without live LLM access"],
        }
    elif "quality" in system.lower():
        payload = {"is_sufficient": True, "confidence": 0.6, "feedback": "[MOCK] Auto-approved offline."}
    elif "discovery questions" in system.lower() or "outreach" in system.lower():
        payload = {
            "discovery_questions": ["[MOCK] What are your current priorities this quarter?"],
            "outreach_strategy": "[MOCK] Lead with a relevant industry trend, offer to discuss pain points.",
            "unknowns": ["[MOCK] Real financials and org structure are unknown without live research."],
        }
    else:
        payload = {"note": "[MOCK] No handler matched; generic placeholder returned."}

    return json.dumps(payload)
