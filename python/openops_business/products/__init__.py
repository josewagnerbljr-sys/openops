# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""Módulo de Produtos do Business OS (Fase 2 do roadmap)."""

from .models import Product
from .repository import ProductRepository, PRODUCTS_MIGRATIONS
from .service import ProductService, MODULE_INFO, register

__all__ = [
    "Product",
    "ProductRepository",
    "PRODUCTS_MIGRATIONS",
    "ProductService",
    "MODULE_INFO",
    "register",
]
