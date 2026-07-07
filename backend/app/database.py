"""
Persistence layer.

Uses SQLite via SQLAlchemy for zero-setup local persistence. Swapping to
Postgres in production is a one-line DATABASE_URL change since no
SQLite-specific features are used.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from app.config import get_settings

settings = get_settings()

connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class User(Base):
    """A registered user of the copilot."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("ResearchSession", back_populates="user", cascade="all, delete-orphan")


class ResearchSession(Base):
    """A single research request created by the user."""

    __tablename__ = "research_sessions"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    company_name = Column(String, nullable=False)
    website = Column(String, nullable=True)
    objective = Column(Text, nullable=False)

    # Workflow lifecycle: pending -> running -> completed | failed
    status = Column(String, default="pending")
    current_node = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    report = Column(JSON, nullable=True)  # final structured report
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
    steps = relationship(
        "WorkflowStep", back_populates="session", cascade="all, delete-orphan",
        order_by="WorkflowStep.started_at",
    )
    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class WorkflowStep(Base):
    """Node-level execution record — powers the Workflow Progress UI."""

    __tablename__ = "workflow_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("research_sessions.id"))
    node_name = Column(String, nullable=False)
    status = Column(String, default="running")  # running | completed | failed | skipped
    detail = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    session = relationship("ResearchSession", back_populates="steps")


class ChatMessage(Base):
    """Follow-up chat grounded in a session's report."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("research_sessions.id"))
    role = Column(String, nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ResearchSession", back_populates="messages")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()