import json
import logging
import sys
from datetime import datetime, timezone

from flask import g, has_request_context, request
from flask_login import current_user

STANDARD_LOG_RECORD_FIELDS = {
    "args",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


def get_structured_extra_fields(record):
    """Returns only the custom fields added to a log entry."""
    return {
        key: value
        for key, value in record.__dict__.items()
        if key not in STANDARD_LOG_RECORD_FIELDS and not key.startswith("_")
    }


class JsonRequestFormatter(logging.Formatter):
    """Writes logs as JSON with request details."""

    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if has_request_context():
            payload.update(
                {
                    "method": request.method,
                    "path": request.path,
                    "remote_addr": request.headers.get("X-Forwarded-For", request.remote_addr),
                    "request_id": getattr(g, "request_id", None),
                }
            )
            if current_user.is_authenticated:
                payload["user_id"] = current_user.id
                payload["username"] = current_user.username

        extra_fields = get_structured_extra_fields(record)
        payload.update(extra_fields)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload)


def configure_logging(app):
    """Sets up the shared JSON logger for the app."""
    logger = logging.getLogger("helpdeskapp")
    logger.setLevel(getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO))
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonRequestFormatter())
        logger.addHandler(handler)

    app.logger.handlers = logger.handlers
    app.logger.setLevel(logger.level)

    return logger