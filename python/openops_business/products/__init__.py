"""Módulo de Produtos do Business OS (Fase 2 do roadmap)."""

from .models import Product
from .repository import ProductRepository, PRODUCTS_MIGRATIONS
from .service import ProductService, MODULE_INFO, register
from .router import router

__all__ = [
    "Product",
    "ProductRepository",
    "PRODUCTS_MIGRATIONS",
    "ProductService",
    "MODULE_INFO",
    "register",
    "router",
]
