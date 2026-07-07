from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class UserOut(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class SessionCreateRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    website: Optional[str] = Field(None, max_length=500)
    objective: str = Field(..., min_length=1, max_length=1000)


class WorkflowStepOut(BaseModel):
    node_name: str
    status: str
    detail: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionSummaryOut(BaseModel):
    id: str
    company_name: str
    website: Optional[str]
    objective: str
    status: str
    current_node: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionDetailOut(SessionSummaryOut):
    error_message: Optional[str] = None
    report: Optional[dict[str, Any]] = None
    steps: list[WorkflowStepOut] = []

    class Config:
        from_attributes = True


class ProgressOut(BaseModel):
    session_id: str
    status: str
    current_node: Optional[str]
    steps: list[WorkflowStepOut]


class ChatMessageIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class ChatMessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True