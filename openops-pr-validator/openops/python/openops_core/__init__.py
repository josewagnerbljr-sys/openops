"""OpenOps Core — Config, Logging e Events (Fase 1 do roadmap)."""

from .config import OpenOpsConfig, load_config, ConfigError
from .events import Event, EventBus, EventHandlingError
from .logging import LogCategory, get_logger, configure_logging

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
]

__version__ = "0.1.0"
