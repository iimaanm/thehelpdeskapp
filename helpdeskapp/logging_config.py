import json
import logging
import sys
from datetime import datetime, timezone

from flask import g, has_request_context, request
from flask_login import current_user


class JsonRequestFormatter(logging.Formatter):
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

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload)


def configure_logging(app):
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