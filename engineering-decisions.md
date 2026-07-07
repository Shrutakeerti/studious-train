# Engineering Decisions

## 1. LangGraph shape: linear pipeline + one conditional retry loop, not a fully agentic graph

**Decision.** The graph is mostly linear (`plan_research → fetch_website →
analyze_company → assess_business → quality_check → generate_report`), with exactly one
conditional edge: `quality_check` can loop back to `analyze_company` once if the
research is flagged insufficient.

**Alternatives considered.**
- A fully agentic graph where an LLM "planner" decides which node to call next at every
  step (tool-calling agent style), with the model choosing whether to research more,
  re-analyze, or finish.
- A branching graph that runs `analyze_company` and `assess_business` in parallel as
  independent branches that merge before `quality_check`.

**Tradeoffs and why.** A fully agentic router is more impressive-sounding but much
harder to debug, test, and bound in cost/latency — for a 2-day assignment where
"recoverability" and "failure handling" are explicitly graded, a deterministic pipeline
with one well-defined loop is more reliable and easier to reason about, and it still
clearly demonstrates conditional routing and shared state. I considered the parallel
branch structure too, since `analyze_company` and `assess_business` don't strictly
depend on each other's LLM output — but `assess_business`'s prompt is noticeably better
grounded when it has the finished company overview and product list to reference, so I
kept them sequential rather than parallelizing for a marginal latency win.

## 2. LLM abstraction with a built-in offline mock fallback

**Decision.** `app/llm.py` wraps every LLM call behind a single `call_llm()` function.
If `GROQ_API_KEY` isn't set, it transparently returns deterministic, clearly-labeled
mock JSON instead of raising or requiring a key.

**Alternatives considered.**
- Requiring a real API key and failing fast/loudly if one isn't configured.
- Building a small test-only mode gated behind an environment flag rather than an
  automatic fallback.

**Tradeoffs and why.** Requiring a live key is simpler code, but it means anyone
reviewing this submission without immediately configuring credentials can't see the
workflow, persistence layer, progress UI, or chat actually run — which is most of what's
being graded. The automatic fallback adds real surface area (a `_mock_response` function
that has to stay loosely in sync with each node's expected JSON shape) purely to make
the submission reviewable with zero setup friction. The cost is that the mock content is
obviously fake, so it doesn't showcase output quality — that's an acceptable tradeoff
given the goal is demonstrating the system works, not demonstrating prompt quality in
the mock path.

## 3. Background task execution + polling instead of a synchronous request or websockets

**Decision.** Session creation returns immediately (`status=pending`) and the LangGraph
workflow runs in a FastAPI `BackgroundTasks` job; the frontend polls a `/progress`
endpoint every 1.5 seconds until the session reaches a terminal status.

**Alternatives considered.**
- Running the workflow synchronously inside the `POST /api/sessions` request and
  blocking until it finishes.
- Using websockets or server-sent events to push progress updates instead of polling.

**Tradeoffs and why.** A synchronous request would time out or feel broken for a
multi-LLM-call workflow that can take 10–30+ seconds, and it gives no way to render a
step-by-step progress UI (an explicit requirement). Websockets/SSE would give snappier
updates with less wasted request volume, but add real complexity (connection lifecycle,
reconnect handling) for a 2-day build where the UX difference between "updates every
1.5s" and "instant push" is minor. Polling was the pragmatic choice; it's also the
easier one to make robust to a page refresh mid-run, since the frontend just re-fetches
current state rather than needing to re-establish a stream.

## What I'd improve with 2 additional weeks

- Replace the single-website fetch with a real research/search step (see
  `product-improvements.md`, priority #1) — this is the highest-leverage change to
  output quality.
- Move workflow execution off in-process `BackgroundTasks` onto a durable queue
  (Celery/RQ) or a LangGraph checkpointer, so long-running or in-flight sessions survive
  a server restart and can be retried at the node level rather than from scratch.
- Add per-claim source attribution in the report (not just a flat source list), and
  surface the model's own uncertainty per section rather than a single overall
  confidence score.
- Harden secrets management: replace the hardcoded `JWT_SECRET_KEY` fallback with a
  required, randomly-generated production value (fail startup if unset outside `dev`),
  and move secrets out of `.env` into a real secrets manager before any real user data
  touches this.
- Write real automated tests (unit tests for each node's fallback path, an integration
  test that runs the full graph against the mock LLM, and frontend component tests) —
  everything in this submission was verified manually end-to-end, which was sufficient
  for the assignment timeline but isn't how I'd want this to ship.