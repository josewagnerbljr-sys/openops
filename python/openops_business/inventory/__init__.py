"""Módulo de Estoque do Business OS (Fase 2 do roadmap)."""

from .models import StockMovement, apply_movement, MOVEMENT_TYPES
from .repository import StockMovementRepository, INVENTORY_MIGRATIONS
from .service import InventoryService, MODULE_INFO, register, LOW_STOCK_THRESHOLD
from .router import router

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
    "router",
]
