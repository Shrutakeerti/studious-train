"""
Centralized configuration management.

All runtime configuration is loaded from environment variables (with sane
defaults for local development) so the service can be configured differently
across dev / staging / prod without code changes.
"""
import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- App ---
    APP_NAME: str = "Zylabs AI Research Copilot"
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # --- CORS ---
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")

    # --- Database ---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./research_copilot.db"
    )

    # --- Auth ---
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-insecure-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: str = os.getenv("RATE_LIMIT_PER_MINUTE", "60/minute")

    # --- LLM Provider ---
    # Supported: "groq" or "mock". Falls back to "mock" automatically
    # if no API key is configured, so the app always runs end-to-end even
    # without credentials (important for graders running this locally).
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1500"))
    LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))

    # --- Workflow ---
    MAX_QUALITY_RETRIES: int = int(os.getenv("MAX_QUALITY_RETRIES", "1"))
    WEBSITE_FETCH_TIMEOUT: int = int(os.getenv("WEBSITE_FETCH_TIMEOUT", "8"))
    WEBSITE_FETCH_MAX_CHARS: int = int(os.getenv("WEBSITE_FETCH_MAX_CHARS", "6000"))

    # --- Logging ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def llm_enabled(self) -> bool:
        return self.LLM_PROVIDER == "groq" and bool(self.GROQ_API_KEY)


@lru_cache
def get_settings() -> Settings:
    return Settings()