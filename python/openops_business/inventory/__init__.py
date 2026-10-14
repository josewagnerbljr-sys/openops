# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""Módulo de Estoque do Business OS (Fase 2 do roadmap)."""

from .models import StockMovement, apply_movement, MOVEMENT_TYPES
from .repository import StockMovementRepository, INVENTORY_MIGRATIONS
from .service import InventoryService, MODULE_INFO, register, LOW_STOCK_THRESHOLD

__all__ = [
    "StockMovement",
    "apply_movement",
    "MOVEMENT_TYPES",
    "StockMovementRepository",
    "INVENTORY_MIGRATIONS",
    "InventoryService",
    "MODULE_INFO",
    "register",
    "LOW_STOCK_THRESHOLD",
]
