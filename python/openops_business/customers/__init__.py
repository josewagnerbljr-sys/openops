"""Módulo de Clientes do Business OS (Fase 2 do roadmap)."""

from .models import Customer
from .repository import CustomerRepository, CUSTOMERS_MIGRATIONS
from .service import CustomerService, MODULE_INFO, register
from .router import router

__all__ = [
    "Customer",
    "CustomerRepository",
    "CUSTOMERS_MIGRATIONS",
    "CustomerService",
    "MODULE_INFO",
    "register",
    "router",
]
