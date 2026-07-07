from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.auth import get_current_user
from app.database import ChatMessage, ResearchSession, User, get_db
from app.llm import LLMError, call_llm
from app.logging_config import get_logger
from app.schemas import ChatMessageIn, ChatMessageOut

router = APIRouter(prefix="/api/sessions", tags=["chat"])
logger = get_logger(__name__)


def _build_system_prompt(session: ResearchSession) -> str:
    report = session.report or {}
    return (
        "You are a sales research copilot answering follow-up questions from a "
        "seller who is preparing for a meeting. Answer ONLY using the research "
        "report context below plus reasonable inference. If something isn't covered, "
        "say so honestly rather than inventing facts.\n\n"
        f"Company: {session.company_name}\n"
        f"Objective: {session.objective}\n"
        f"Report JSON: {report}"
    )


def _get_owned_session(session_id: str, user: User, db: DBSession) -> ResearchSession:
    session = (
        db.query(ResearchSession)
        .filter(ResearchSession.id == session_id, ResearchSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/{session_id}/chat", response_model=list[ChatMessageOut])
def get_chat_history(session_id: str, db: DBSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = _get_owned_session(session_id, current_user, db)
    return session.messages


@router.post("/{session_id}/chat", response_model=ChatMessageOut)
def send_chat_message(
    session_id: str,
    payload: ChatMessageIn,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = _get_owned_session(session_id, current_user, db)
    if session.status != "completed":
        raise HTTPException(
            status_code=409,
            detail="Report is not ready yet — chat is available once the research workflow completes.",
        )

    user_msg = ChatMessage(session_id=session_id, role="user", content=payload.message)
    db.add(user_msg)
    db.commit()

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    convo = "\n".join(f"{m.role.upper()}: {m.content}" for m in history[-10:])

    try:
        reply_text = call_llm(_build_system_prompt(session), convo)
    except LLMError as exc:
        logger.error("Chat LLM call failed for session %s: %s", session_id, exc)
        reply_text = (
            "Sorry, I couldn't generate a response right now due to a temporary "
            "issue with the research assistant. Please try again."
        )

    assistant_msg = ChatMessage(session_id=session_id, role="assistant", content=reply_text)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    return assistant_msg