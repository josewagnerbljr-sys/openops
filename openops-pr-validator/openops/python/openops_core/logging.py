"""
openops_core.logging
=====================

Logging estruturado (JSON Lines) para o OpenOps. Cada log carrega uma
categoria (LogCategory) para permitir filtragem por camada — Business,
Security, Maintenance, Health, etc. — o que facilita tanto auditoria
quanto o consumo por ferramentas externas (dashboards, SIEM).
"""

from __future__ import annotations

import json
import logging as _stdlib_logging
import sys
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class LogCategory(str, Enum):
    """Categoria funcional do log, alinhada às camadas do OpenOps."""

    CORE = "core"
    BUSINESS = "business"
    SOP = "sop"
    OPERATIONS = "operations"
    SECURITY = "security"
    MAINTENANCE = "maintenance"
    HEALTH = "health"
    PLUGIN = "plugin"
    API = "api"


class JsonFormatter(_stdlib_logging.Formatter):
    """Formata cada registro de log como uma linha JSON (JSON Lines)."""

    def format(self, record: _stdlib_logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "category": getattr(record, "category", LogCategory.CORE.value),
        }

        extra_fields = getattr(record, "fields", None)
        if extra_fields:
            payload["fields"] = extra_fields

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


class OpenOpsLogger:
    """Wrapper fino sobre ``logging.Logger`` que exige uma categoria por chamada."""

    def __init__(self, name: str) -> None:
        self._logger = _stdlib_logging.getLogger(name)

    def _log(
        self,
        level: int,
        message: str,
        category: LogCategory,
        **fields: Any,
    ) -> None:
        self._logger.log(
            level,
            message,
            extra={"category": category.value, "fields": fields or None},
        )

    def debug(self, message: str, *, category: LogCategory = LogCategory.CORE, **fields: Any) -> None:
        self._log(_stdlib_logging.DEBUG, message, category, **fields)

    def info(self, message: str, *, category: LogCategory = LogCategory.CORE, **fields: Any) -> None:
        self._log(_stdlib_logging.INFO, message, category, **fields)

    def warning(self, message: str, *, category: LogCategory = LogCategory.CORE, **fields: Any) -> None:
        self._log(_stdlib_logging.WARNING, message, category, **fields)

    def error(self, message: str, *, category: LogCategory = LogCategory.CORE, **fields: Any) -> None:
        self._log(_stdlib_logging.ERROR, message, category, **fields)


def configure_logging(level: str = "INFO") -> None:
    """Configura o handler raiz do processo para emitir JSON em stdout.

    Idempotente: chamadas repetidas não duplicam handlers.
    """

    root = _stdlib_logging.getLogger()
    root.setLevel(level)

    if any(isinstance(h.formatter, JsonFormatter) for h in root.handlers):
        return

    handler = _stdlib_logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)


def get_logger(name: str) -> OpenOpsLogger:
    """Obtém um logger estruturado do OpenOps para o módulo ``name``."""

    return OpenOpsLogger(name)
