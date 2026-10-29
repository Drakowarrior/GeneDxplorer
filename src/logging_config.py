import logging
import sys
from contextvars import ContextVar
from typing import Optional

# ContextVar to store request ID across async tasks & threads
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

def get_request_id() -> str:
    return request_id_ctx.get()

def set_request_id(req_id: str):
    request_id_ctx.set(req_id)

class RequestIDFilter(logging.Filter):
    """
    Logging filter that injects request_id from ContextVar into log records.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True

class SecretMaskingFormatter(logging.Formatter):
    """
    Formatter that redacts sensitive API keys and secrets from log messages.
    """
    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        # Redact potential API keys or secrets if present
        if "api_key" in formatted.lower() or "apikey" in formatted.lower():
            # Basic key pattern masking
            import re
            formatted = re.sub(r'(api_key|apikey)=([a-zA-Z0-9_\-]+)', r'\1=***REDACTED***', formatted, flags=re.IGNORECASE)
        return formatted

def setup_logging(log_level: str = "INFO"):
    """
    Initialize application structured logging configuration.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if already configured
    if root_logger.handlers:
        root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = SecretMaskingFormatter(
        fmt="[%(asctime)s] [%(levelname)s] [req_id=%(request_id)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())
    
    root_logger.addHandler(handler)

    # Adjust noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
