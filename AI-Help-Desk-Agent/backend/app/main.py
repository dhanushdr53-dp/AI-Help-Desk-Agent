from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from .config import settings
from .database import Base, engine, get_db, SessionLocal
from .models import User, Conversation, Message, Ticket, KnowledgeDocument, SystemService, Notification, AuditLog
from .schemas import AuthInput, Token, UserOut, ChatInput, ChatOutput, TicketCreate, TicketUpdate, TicketOut, KnowledgeCreate
from .security import hash_password, verify_password, create_token, current_user, require_admin
from .agent import run_agent, make_ticket, sla_for


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter_by(email="demo@helpdesk.local").first():
            db.add(User(
                email="demo@helpdesk.local",
                name="Demo Admin",
                password_hash=hash_password("demo1234"),
                role="admin",
            ))
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="AI Help Desk Agent API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",")],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ai-help-desk-agent"}


@app.post("/api/auth/register", response_model=Token)
def register(payload: AuthInput, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=payload.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    user = User(email=payload.email.lower(), name=payload.name, password_hash=hash_password(payload.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"access_token": create_token(user), "user": user}


@app.post("/api/auth/login", response_model=Token)
def login(payload: AuthInput, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": create_token(user), "user": user}


@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@app.post("/api/chat", response_model=ChatOutput)
def chat(payload: ChatInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    conversation = db.get(Conversation, payload.conversation_id) if payload.conversation_id else None
    if conversation and conversation.user_id != user.id:
        raise HTTPException(403, "Conversation access denied")
    if not conversation:
        conversation = Conversation(user_id=user.id, title=payload.message[:60])
        db.add(conversation); db.commit(); db.refresh(conversation)
    db.add(Message(conversation_id=conversation.id, role="user", content=payload.message))
    result = run_agent(db, user, payload.message)
    db.add(Message(conversation_id=conversation.id, role="assistant", content=result["answer"]))
    db.commit()
    return {**result, "conversation_id": conversation.id}


@app.get("/api/conversations")
def conversations(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(Conversation).filter_by(user_id=user.id).order_by(Conversation.created_at.desc()).all()
    return [{"id": x.id, "title": x.title, "created_at": x.created_at} for x in rows]


@app.get("/api/tickets", response_model=list[TicketOut])
def tickets(db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = db.query(Ticket)
    if user.role != "admin":
        query = query.filter(Ticket.requester_id == user.id)
    return query.order_by(Ticket.created_at.desc()).all()


@app.post("/api/tickets", response_model=TicketOut)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return make_ticket(db, user, payload.title, payload.description, payload.category, payload.priority)


@app.put("/api/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: str, payload: TicketUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    ticket = db.query(Ticket).filter_by(ticket_id=ticket_id).first()
    if not ticket or (user.role != "admin" and ticket.requester_id != user.id):
        raise HTTPException(404, "Ticket not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ticket, field, value)
    db.add(AuditLog(actor_id=user.id, action="ticket.updated", detail=ticket.ticket_id))
    db.commit(); db.refresh(ticket)
    return ticket


@app.post("/api/tickets/{ticket_id}/escalate", response_model=TicketOut)
def escalate(ticket_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    ticket = db.query(Ticket).filter_by(ticket_id=ticket_id).first()
    if not ticket or (user.role != "admin" and ticket.requester_id != user.id):
        raise HTTPException(404, "Ticket not found")
    ticket.status, ticket.assigned_agent = "ESCALATED", "Supervisor Queue"
    db.add(AuditLog(actor_id=user.id, action="ticket.escalated", detail=ticket.ticket_id))
    db.commit(); db.refresh(ticket)
    return ticket


@app.get("/api/system/status")
def system_status(db: Session = Depends(get_db)):
    return [{"name": x.name, "status": x.status, "message": x.message, "updated_at": x.updated_at} for x in db.query(SystemService).all()]


@app.get("/api/knowledge")
def knowledge(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return [{"id": x.id, "title": x.title, "category": x.category, "source": x.source} for x in db.query(KnowledgeDocument).all()]


@app.post("/api/knowledge")
def add_knowledge(payload: KnowledgeCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    item = KnowledgeDocument(**payload.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item


@app.get("/api/notifications")
def notifications(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.query(Notification).filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()


@app.get("/api/admin/analytics")
def analytics(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return {
        "total_tickets": db.query(Ticket).count(),
        "open_tickets": db.query(Ticket).filter(Ticket.status.in_(["OPEN", "IN_PROGRESS", "ESCALATED"])).count(),
        "critical_tickets": db.query(Ticket).filter(Ticket.priority == "CRITICAL").count(),
        "resolved_tickets": db.query(Ticket).filter(Ticket.status.in_(["RESOLVED", "CLOSED"])).count(),
        "knowledge_articles": db.query(KnowledgeDocument).count(),
        "active_users": db.query(User).count(),
    }