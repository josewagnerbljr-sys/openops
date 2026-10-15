# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""Módulo de Clientes do Business OS (Fase 2 do roadmap)."""

from .models import Customer
from .repository import CustomerRepository, CUSTOMERS_MIGRATIONS
from .service import CustomerService, MODULE_INFO, register

__all__ = [
    "Customer",
    "CustomerRepository",
    "CUSTOMERS_MIGRATIONS",
    "CustomerService",
    "MODULE_INFO",
    "register",
]
