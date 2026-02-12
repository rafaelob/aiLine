from __future__ import annotations

import logging
from typing import Any

import structlog


def configure_logging(*, json_output: bool = True, level: str = "INFO") -> None:
    """Configure structlog for structured JSON logging."""
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_output:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[*shared_processors, renderer],
        )
    )

    root_logger = logging.getLogger()
    # Avoid accumulating handlers on repeated calls
    if not any(
        isinstance(h, logging.StreamHandler)
        and isinstance(getattr(h, "formatter", None), structlog.stdlib.ProcessorFormatter)
        for h in root_logger.handlers
    ):
        root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger


def log_event(name: str, **data: Any) -> None:
    """Log a pipeline event."""
    logger = get_logger("ailine.events")
    logger.info(name, **data)
