# Architecture

## 1. System diagram

```
┌─────────────────┐      HTTP/JSON        ┌──────────────────────────┐
│   React (Vite)   │ ────────────────────▶ │      FastAPI backend     │
│  - Login/Signup   │ ◀──────────────────── │  - /api/auth (JWT)       │
│  - Session form    │                      │  - /api/sessions         │
│  - Progress poll    │                     │  - /api/sessions/{id}/   │
│  - Report view       │                    │      progress, chat      │
│  - Chat panel          │                  └────────────┬─────────────┘
└─────────────────┘                                       │ background task
                                                           ▼
                                             ┌──────────────────────────┐
                                             │     LangGraph workflow    │
                                             │                            │
                                             │  plan_research             │
                                             │       │                    │
                                             │  fetch_website              │
                                             │       │                    │
                                             │  analyze_company ◀──┐       │
                                             │       │             │       │
                                             │  assess_business    │       │
                                             │       │             │       │
                                             │  quality_check ──retry──────┘
                                             │       │ proceed
                                             │  generate_report            │
                                             └────────────┬─────────────┘
                                                           │ LLM calls
                                                           ▼
                                             ┌──────────────────────────┐
                                             │   Groq API (or       │
                                             │   offline mock fallback)  │
                                             └──────────────────────────┘
                                                           │
                                                           ▼
                                             ┌──────────────────────────┐
                                             │   SQLite (SQLAlchemy)     │
                                             │  users / sessions /       │
                                             │  steps / chat             │
                                             └──────────────────────────┘
```

## 2. Layers

**Frontend (React + Vite).** A single-page app with a login/signup flow, a home page
(session creation + history), a session detail page (workflow progress, report, chat),
and a router shell that redirects unauthenticated users via `ProtectedRoute`. Vite was
chosen over Create React App because it's the current standard — fast dev server, no
config overhead, and a one-line proxy setup to avoid CORS friction during local
development. State is managed with plain React hooks (`useState`/`useEffect`) and a
small `AuthContext` rather than a state library, since the app has few real screens and
no cross-cutting shared state beyond the current user and what's fetched per-page.

**Backend (FastAPI).** FastAPI was chosen for its native async support, automatic
OpenAPI docs (useful for a 2-day assignment where I don't want to hand-write API docs),
and first-class Pydantic validation. The backend exposes auth (signup/login/me), session
CRUD, a progress endpoint the frontend polls, and a chat endpoint. Every session-scoped
endpoint checks ownership against the authenticated user (`_get_owned_session`), and a
per-IP rate limit (`slowapi`) protects the LLM-backed endpoints from accidental or
abusive request floods. Workflow execution runs in a `BackgroundTasks` job so session
creation returns immediately and the frontend can show a progress UI rather than
blocking on a single long HTTP request.

**AI workflow (LangGraph).** This is the core of the assignment. A `StateGraph` threads
a single shared `ResearchState` dict through six nodes: `plan_research` (LLM),
`fetch_website` (plain HTTP + HTML parsing, no LLM), `analyze_company` (LLM),
`assess_business` (LLM), `quality_check` (LLM, drives conditional routing), and
`generate_report` (LLM). `quality_check` uses a conditional edge: if the reviewer flags
the research as insufficient and a retry budget remains, the graph loops back to
`analyze_company` with the reviewer's feedback appended to the prompt; otherwise it
proceeds to `generate_report`. Every node is wrapped in a try/except that records the
error into `state["node_errors"]` and substitutes a safe fallback value rather than
crashing the graph — this is what "failure handling" and "recoverability" mean in
practice here: a single flaky LLM call degrades one section of the report instead of
losing the whole session.

**Storage (SQLite via SQLAlchemy).** Four tables: `users` (auth), `research_sessions`
(the session record + final report JSON, owned by a user), `workflow_steps` (one row
per completed node, which is literally what powers the Workflow Progress UI), and
`chat_messages`. SQLite was chosen purely for zero-setup local development; because no
SQLite-specific features are used, switching `DATABASE_URL` to Postgres is the only
change needed for production.

## 3. Data flow, end to end

1. User signs up / logs in; the frontend stores the returned JWT and attaches it to
   subsequent requests.
2. User submits company name, website, and objective on the frontend.
3. `POST /api/sessions` creates a `research_sessions` row owned by the authenticated
   user with `status=pending`, schedules `_execute_workflow` as a background task, and
   returns immediately.
4. The frontend redirects to the session detail page and begins polling
   `GET /api/sessions/{id}/progress` every 1.5s.
5. `_execute_workflow` sets `status=running`, builds the initial `ResearchState`, and
   calls `run_workflow_streaming`, which drives the compiled LangGraph graph node by
   node using `.stream(..., stream_mode="updates")`.
6. After each node finishes, a callback persists a `workflow_steps` row and updates
   `current_node` — this is what the frontend's progress timeline reflects in near
   real time.
7. Once `generate_report` completes, the accumulated state's `final_report` is written
   to `research_sessions.report` and `status` flips to `completed`.
8. The frontend's poll loop sees `status=completed`, stops polling, and renders the
   structured `ReportView`. The chat panel becomes available.
9. Follow-up chat messages are sent to `POST /api/sessions/{id}/chat`, which builds a
   system prompt from the session's report JSON, calls the LLM with the last 10 turns
   of conversation history, and persists both the user and assistant messages.

## 4. Notable tradeoffs and constraints

- **No external search API.** Rather than depending on a paid search API (Serp API,
  Tavily, etc.) that a grader might not have credentials for, the `fetch_website` node
  does direct HTTP fetch + HTML text extraction from the company's own site. This is a
  real tradeoff: the copilot's grounding is limited to what the company's homepage says
  plus the LLM's own knowledge, rather than broad web research. Swapping in a search
  tool is a contained change — it would slot in as a new node between `plan_research`
  and `analyze_company`.
- **Mock LLM fallback.** Building an offline mock path added real code (`app/llm.py`)
  that wouldn't exist in a pure production system, but it means the entire assignment —
  workflow, persistence, UI, chat — can be verified by a grader with zero API credentials
  and zero flakiness from live model calls during review.
- **Background tasks over a task queue.** `BackgroundTasks` is in-process and doesn't
  survive a server restart mid-run. For a 2-day assignment this is an acceptable
  tradeoff; a production version would use Celery/RQ or a durable LangGraph checkpointer
  so in-flight workflows can resume after a deploy.
- **Polling over websockets/SSE.** Progress is polled every 1.5s rather than pushed.
  Simpler to implement and debug, at the cost of slightly delayed UI updates and a bit
  of wasted request volume on longer-running sessions.
- **Single quality-retry loop.** The conditional edge only allows the graph to loop back
  once by default (`MAX_QUALITY_RETRIES=1`) to keep worst-case latency and LLM cost
  bounded, at the cost of occasionally shipping a report the reviewer node considered
  imperfect.
- **Secrets are dev-friendly, not production-safe by default.** `JWT_SECRET_KEY` has a
  hardcoded fallback so the app boots with zero configuration, and `.env` (git-ignored)
  is the only place secrets live — there's no secrets manager or key rotation. That's a
  reasonable tradeoff for a 2-day local-first submission, but it's a hard requirement to
  fix (real random secret, proper secrets store) before this touches real user data.