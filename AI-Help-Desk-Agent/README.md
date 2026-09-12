# AI Help Desk Agent

An agentic IT help-desk starter project built around **FastAPI + React + Gemini**.
It understands support requests, classifies intent, searches a small knowledge base,
checks service status, creates tickets, calculates SLA, and keeps the workflow visible
in the UI.

## Included

- Gemini provider abstraction (`GeminiProvider`) with structured JSON responses.
- Safe local fallback when `GEMINI_API_KEY` is not configured, so the demo is runnable.
- Agent workflow: understand → classify → plan → tools → verify → respond.
- Knowledge search with chunking-ready local retrieval.
- Ticket lifecycle, priorities, SLA deadlines, escalation, and audit events.
- System status API and dashboard.
- React/Vite frontend with chat, tickets, system status, and analytics cards.
- SQLite by default; PostgreSQL-ready through `DATABASE_URL`.
- Docker Compose, seed data, API docs, and pytest tests.

## Run locally

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The API documentation is at
`http://localhost:8000/docs`.

Demo login: `demo@helpdesk.local` / `demo1234`

To enable real Gemini responses, put a key in `backend/.env`:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
```

Keys stay on the backend and are never sent to React.

## Docker

```bash
docker compose up --build
```

The frontend is served at `http://localhost:5173` and the API at
`http://localhost:8000`.

## Architecture

```text
React UI
  ↓
FastAPI REST API ── JWT/RBAC ── SQLAlchemy
  ↓
Agent Orchestrator
  ├─ Intent classifier
  ├─ Knowledge retrieval
  ├─ System status tool
  ├─ Ticket tool
  └─ Gemini provider (optional but production path)
  ↓
Validated structured response + citations + audit event
```

The tool registry uses an allow-list and validates arguments before execution.
High-risk actions such as ticket creation and escalation are only triggered by an
explicit request in this starter. Add confirmation tokens before exposing those
actions to untrusted production clients.

## API highlights

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Create an account |
| POST | `/api/auth/login` | Get a JWT |
| POST | `/api/chat` | Run the agent |
| GET | `/api/tickets` | List tickets |
| POST | `/api/tickets` | Create a ticket |
| POST | `/api/tickets/{id}/escalate` | Escalate a ticket |
| GET | `/api/system/status` | Live service status |
| GET | `/api/knowledge` | List knowledge articles |
| POST | `/api/knowledge` | Add a knowledge article |
| GET | `/api/admin/analytics` | Dashboard metrics |

## Next production steps

Replace local retrieval with ChromaDB embeddings, add Redis rate limiting and
Celery workers, wire email notifications, add Alembic migrations, and place the
backend behind HTTPS with a managed PostgreSQL instance.