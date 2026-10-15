# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
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
import os
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


def configure_logging(level: str = "INFO", *, log_file: str | None = None) -> None:
    """Configura o handler raiz do processo para emitir JSON em stdout e,
    opcionalmente, também em um arquivo (``log_file``, ex.: ``openops.log``)
    — o registro persistente que permite auditar o que foi feito depois que
    o terminal foi fechado.

    Idempotente: chamadas repetidas não duplicam handlers.
    """

    root = _stdlib_logging.getLogger()
    root.setLevel(level)

    if not any(isinstance(h.formatter, JsonFormatter) and not isinstance(h, _stdlib_logging.FileHandler)
               for h in root.handlers):
        handler = _stdlib_logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(JsonFormatter())
        root.addHandler(handler)

    if log_file is not None:
        wanted = os.path.abspath(log_file)
        already = any(
            isinstance(h, _stdlib_logging.FileHandler) and h.baseFilename == wanted
            for h in root.handlers
        )
        if not already:
            file_handler = _stdlib_logging.FileHandler(wanted, encoding="utf-8")
            file_handler.setFormatter(JsonFormatter())
            root.addHandler(file_handler)


def get_logger(name: str) -> OpenOpsLogger:
    """Obtém um logger estruturado do OpenOps para o módulo ``name``."""

    return OpenOpsLogger(name)
