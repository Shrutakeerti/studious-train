"""
Structured logging setup. Every log line is prefixed with a timestamp,
level, and logger name so workflow execution can be traced end-to-end
across nodes and requests — critical for debugging a multi-node LangGraph
pipeline in production.
"""
import logging
import sys

from app.config import get_settings

settings = get_settings()


def configure_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        # Already configured (e.g. reload) — avoid duplicate handlers.
        return

    root.setLevel(settings.LOG_LEVEL)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Quiet down noisy third-party loggers.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
