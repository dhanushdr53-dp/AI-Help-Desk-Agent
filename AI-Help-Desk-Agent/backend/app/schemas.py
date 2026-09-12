from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AuthInput(BaseModel):
    email: str
    password: str = Field(min_length=6)
    name: str = "Support User"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    name: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ChatInput(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: int | None = None


class ChatOutput(BaseModel):
    answer: str
    intent: str
    priority: str
    confidence: float
    action_required: bool = False
    action: str | None = None
    ticket_id: str | None = None
    sources: list[str] = []
    tool_trace: list[str] = []
    conversation_id: int


class TicketCreate(BaseModel):
    title: str
    description: str
    category: str = "general"
    priority: str = "MEDIUM"


class TicketUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    resolution: str | None = None


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticket_id: str
    title: str
    description: str
    category: str
    priority: str
    status: str
    assigned_agent: str | None
    sla_deadline: datetime | None
    resolution: str | None
    created_at: datetime


class KnowledgeCreate(BaseModel):
    title: str
    content: str
    category: str = "general"
    source: str = "internal"