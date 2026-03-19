import logging
import sys
from typing import Any

from app.core.config import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""

    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
    ]

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=log_format,
        handlers=handlers,
        force=True,
    )

    if settings.is_production:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    else:
        logging.getLogger("uvicorn.access").setLevel(logging.INFO)
        logging.getLogger("uvicorn.error").setLevel(logging.DEBUG)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin to add logger to any class."""

    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, "_logger"):
            self._logger = get_logger(
                self.__class__.__module__ + "." + self.__class__.__name__
            )
        return self._logger
