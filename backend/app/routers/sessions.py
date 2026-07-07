from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.auth import get_current_user
from app.database import ResearchSession, User, WorkflowStep, get_db
from app.graph.workflow import run_workflow_streaming
from app.logging_config import get_logger
from app.schemas import ProgressOut, SessionCreateRequest, SessionDetailOut, SessionSummaryOut

router = APIRouter(prefix="/api/sessions", tags=["sessions"])
logger = get_logger(__name__)

# Human-readable status detail shown per node in the UI.
NODE_LABELS = {
    "plan_research": "Planning research approach",
    "fetch_website": "Fetching company website",
    "analyze_company": "Analyzing company overview & products",
    "assess_business": "Assessing business signals & risks",
    "quality_check": "Reviewing research quality",
    "increment_retry": "Refining research (quality retry)",
    "generate_report": "Generating final report",
}


def _execute_workflow(session_id: str):
    """
    Runs in a background task. Uses its own DB session since it executes
    outside the request/response lifecycle.
    """
    from app.database import SessionLocal

    db: DBSession = SessionLocal()
    try:
        session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
        if not session:
            logger.error("Session %s vanished before workflow could run", session_id)
            return

        session.status = "running"
        db.commit()

        def on_step(node_name: str, updates: dict):
            step = WorkflowStep(
                session_id=session_id,
                node_name=node_name,
                status="failed" if updates.get("node_errors", {}).get(node_name) else "completed",
                detail=NODE_LABELS.get(node_name, node_name),
                finished_at=datetime.utcnow(),
            )
            db.add(step)
            session.current_node = node_name
            db.commit()

        initial_state = {
            "session_id": session_id,
            "company_name": session.company_name,
            "website": session.website,
            "objective": session.objective,
            "retry_count": 0,
        }

        final_state = run_workflow_streaming(initial_state, on_step)

        session.report = final_state.get("final_report", {})
        session.status = "completed"
        session.current_node = None
        db.commit()
        logger.info("Session %s workflow completed", session_id)

    except Exception as exc:
        logger.exception("Session %s workflow failed hard: %s", session_id, exc)
        session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
        if session:
            session.status = "failed"
            session.error_message = str(exc)
            db.commit()
    finally:
        db.close()


def _get_owned_session(session_id: str, user: User, db: DBSession) -> ResearchSession:
    session = (
        db.query(ResearchSession)
        .filter(ResearchSession.id == session_id, ResearchSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("", response_model=SessionDetailOut, status_code=201)
def create_session(
    payload: SessionCreateRequest,
    background_tasks: BackgroundTasks,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = ResearchSession(
        user_id=current_user.id,
        company_name=payload.company_name,
        website=payload.website,
        objective=payload.objective,
        status="pending",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    background_tasks.add_task(_execute_workflow, session.id)
    logger.info("User %s created session %s for company '%s'", current_user.id, session.id, session.company_name)
    return session


@router.get("", response_model=list[SessionSummaryOut])
def list_sessions(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = (
        db.query(ResearchSession)
        .filter(ResearchSession.user_id == current_user.id)
        .order_by(ResearchSession.created_at.desc())
        .all()
    )
    return sessions


@router.get("/{session_id}", response_model=SessionDetailOut)
def get_session(session_id: str, db: DBSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_owned_session(session_id, current_user, db)


@router.get("/{session_id}/progress", response_model=ProgressOut)
def get_progress(session_id: str, db: DBSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = _get_owned_session(session_id, current_user, db)
    return ProgressOut(
        session_id=session.id,
        status=session.status,
        current_node=session.current_node,
        steps=session.steps,
    )


@router.post("/{session_id}/rerun", response_model=SessionDetailOut)
def rerun_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = _get_owned_session(session_id, current_user, db)

    # Clear prior steps/report for a clean re-run (recoverability).
    for step in list(session.steps):
        db.delete(step)
    session.status = "pending"
    session.error_message = None
    session.report = None
    session.current_node = None
    db.commit()
    db.refresh(session)

    background_tasks.add_task(_execute_workflow, session.id)
    return session


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: str, db: DBSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = _get_owned_session(session_id, current_user, db)
    db.delete(session)
    db.commit()
    return None