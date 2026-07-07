from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.database import init_db
from app.logging_config import configure_logging, get_logger
from app.routers import auth, chat, sessions

configure_logging()
logger = get_logger(__name__)
settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_PER_MINUTE])

app = FastAPI(
    title=settings.APP_NAME,
    description="AI Research Copilot for sales meeting preparation, powered by LangGraph.",
    version="1.1.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info(
        "%s starting up | env=%s | llm_enabled=%s",
        settings.APP_NAME,
        settings.ENV,
        settings.llm_enabled,
    )
    if not settings.llm_enabled:
        logger.warning(
            "No GROQ_API_KEY configured — LLM nodes will return mock content. "
            "Set GROQ_API_KEY in .env for real research output."
        )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s: %s", request.method, request.url, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."},
    )


@app.get("/api/health")
def health_check():
    return {"status": "ok", "llm_enabled": settings.llm_enabled}


app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(chat.router)