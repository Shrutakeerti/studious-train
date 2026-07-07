# Zylabs AI Research Copilot

An AI-powered research copilot that helps a seller prepare for a meeting: give it a
company, a website, and an objective, and it runs a LangGraph workflow that researches
the company and produces a structured briefing — then stays available for follow-up
questions grounded in that report.

Built for the Zylabs Intern AI Engineer Assignment.

## Stack

- **Frontend:** React (Vite) + React Router
- **Backend:** Python + FastAPI
- **AI workflow:** LangGraph (multi-node graph with conditional routing)
- **Persistence:** SQLite via SQLAlchemy
- **Auth:** JWT-based signup/login (not required by the brief, added so sessions have
  a real owner rather than being anonymous/global)
- **Rate limiting:** per-IP limiting via `slowapi`, since an unauthenticated-cost LLM
  endpoint without any limit is the fastest way to get a surprise bill

## Project structure

```
zylabs-research-copilot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, rate limiting, global error handler
│   │   ├── config.py            # Environment-based configuration
│   │   ├── database.py          # SQLAlchemy models + session factory
│   │   ├── schemas.py           # Pydantic request/response models
│   │   ├── auth.py              # Password hashing + JWT issuance/verification
│   │   ├── llm.py               # LLM client (Groq + offline mock fallback)
│   │   ├── logging_config.py    # Structured logging setup
│   │   ├── graph/
│   │   │   ├── state.py         # Shared LangGraph state definition
│   │   │   ├── nodes.py         # All workflow node implementations
│   │   │   └── workflow.py      # Graph assembly + streaming execution
│   │   └── routers/
│   │       ├── auth.py          # /signup, /login, /me
│   │       ├── sessions.py      # Session CRUD + workflow trigger + progress
│   │       └── chat.py          # Follow-up chat grounded in report
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/          # SessionForm, SessionList, SessionDetail,
│   │   │                        # WorkflowProgress, ReportView, ChatPanel, Login, Signup
│   │   ├── context/AuthContext.jsx
│   │   ├── api.js               # Backend API client
│   │   ├── App.jsx              # Routing shell
│   │   └── styles/index.css     # Design system
│   └── package.json
├── README.md
├── architecture.md
├── product-improvements.md
└── engineering-decisions.md
```

## Running locally

### 1. Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set GROQ_API_KEY if you want live research output, and set a real
# JWT_SECRET_KEY (see Security Notes below — do not use the default in anything
# but local dev).
uvicorn app.main:app --reload --port 8000
```

The API is now available at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

The app is now available at `http://localhost:5173`. Vite proxies `/api` requests to
the backend at `localhost:8000` (see `vite.config.js`), so no additional configuration
is needed.

### 3. Try it

1. Open `http://localhost:5173` and sign up for an account.
2. Fill in a company name, optional website, and a research objective.
3. Watch the workflow progress panel as the LangGraph pipeline runs.
4. Review the structured report once it completes.
5. Ask follow-up questions in the chat panel below the report.

## Configuration

All configuration lives in environment variables — see `backend/.env.example` for the
full list. The most relevant ones:

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Enables live LLM calls. Left blank → offline mock mode. |
| `GROQ_MODEL` | Model name used for all LLM calls. |
| `MAX_QUALITY_RETRIES` | How many times the graph will loop back for a refinement pass if the quality-check node flags the research as insufficient. |
| `DATABASE_URL` | SQLite by default; point at Postgres for production. |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins. |
| `JWT_SECRET_KEY` | Signs auth tokens. **Must** be overridden with a long random value outside local dev — see Security Notes. |
| `RATE_LIMIT_PER_MINUTE` | Per-IP request limit (default `60/minute`) applied to the API. |

## Notes for graders

- The workflow is fully runnable **without** an API key — `app/llm.py` falls back to a
  deterministic mock responder so the LangGraph pipeline, persistence, progress UI, and
  chat can all be exercised end-to-end offline. Set `GROQ_API_KEY` for real output.
- Website fetching (`fetch_website` node) uses `requests` + `BeautifulSoup` directly
  against the provided URL — no external search API dependency required.
- See `architecture.md` for how data flows through the system, `product-improvements.md`
  for known weaknesses and next steps, and `engineering-decisions.md` for the reasoning
  behind the three biggest design decisions.

## Security notes

- **`.env` is git-ignored and must never be committed or shared.** If a real
  `GROQ_API_KEY` or `JWT_SECRET_KEY` ever ends up in a shared zip, repo, or screenshot,
  rotate it immediately — treat it as compromised the moment it leaves your machine.
- **`JWT_SECRET_KEY` ships with an insecure default** (`dev-insecure-secret-change-me`)
  so the app boots with zero setup for local review. This default must never be used
  outside local development — anyone who reads this file could forge tokens against a
  deployment still using it.