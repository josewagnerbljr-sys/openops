"""OpenOps Core — Config, Logging, Events, Errors, Registry e DB (Fase 1 do roadmap)."""

from .config import OpenOpsConfig, load_config, ConfigError
from .events import Event, EventBus, EventHandlingError
from .logging import LogCategory, get_logger, configure_logging
from .errors import (
    OpenOpsError,
    ValidationError,
    NotFoundError,
    ConflictError,
    AuthorizationError,
    ConfigurationError,
    IntegrationError,
    MaintenanceError,
    http_status_for,
)
from .registry import ModuleRegistry, ModuleInfo, register_module, default_registry
from .db import Database, Migration, database

__all__ = [
    "OpenOpsConfig",
    "load_config",
    "ConfigError",
    "Event",
    "EventBus",
    "EventHandlingError",
    "LogCategory",
    "get_logger",
    "configure_logging",
    "OpenOpsError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "AuthorizationError",
    "ConfigurationError",
    "IntegrationError",
    "MaintenanceError",
    "http_status_for",
    "ModuleRegistry",
    "ModuleInfo",
    "register_module",
    "default_registry",
    "Database",
    "Migration",
    "database",
]

__version__ = "0.2.0"
