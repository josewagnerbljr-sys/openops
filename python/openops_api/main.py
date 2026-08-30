"""
openops_api.main
=================

Ponto de entrada da API HTTP do OpenOps (Fase 9 do roadmap, adiantada
como fatia demonstrável junto com o primeiro módulo de Business OS).

``create_app()`` é uma factory, não um singleton global — cada chamada
monta uma instância nova, com seu próprio banco. Isso é o que permite os
testes de API rodarem isolados uns dos outros sem nenhum estado
compartilhado escondido.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from openops_core.db import Database
from openops_core.errors import OpenOpsError, http_status_for
from openops_core.registry import ModuleRegistry, default_registry

from openops_business.products import ProductService
from openops_business.products import router as products_router
from openops_business.products.service import register as register_products

from openops_business.customers import CustomerService
from openops_business.customers import router as customers_router
from openops_business.customers.service import register as register_customers


def create_app(*, db_path: str = ":memory:", registry: ModuleRegistry | None = None) -> FastAPI:
    """Monta uma instância da API OpenOps.

    Args:
        db_path: caminho do arquivo SQLite, ou ``:memory:`` (padrão,
            usado em testes e demonstrações rápidas).
        registry: registry de módulos a usar; por padrão, o
            ``default_registry`` compartilhado do processo.
    """

    app = FastAPI(
        title="OpenOps API",
        description="Open Source Business Operations Platform — API HTTP",
        version="0.1.0",
    )

    target_registry = registry if registry is not None else default_registry

    db = Database(db_path)
    product_service = ProductService(db)
    if "products" not in target_registry:
        register_products(target_registry)

    customer_service = CustomerService(db)
    if "customers" not in target_registry:
        register_customers(target_registry)

    app.state.db = db
    app.state.product_service = product_service
    app.state.customer_service = customer_service
    app.state.registry = target_registry

    @app.exception_handler(OpenOpsError)
    def handle_openops_error(_: Request, exc: OpenOpsError) -> JSONResponse:
        return JSONResponse(status_code=http_status_for(exc), content=exc.to_dict())

    @app.get("/", tags=["meta"])
    def root() -> dict[str, object]:
        return {
            "name": "OpenOps API",
            "modules": [m.name for m in target_registry.list()],
        }

    app.include_router(products_router)
    app.include_router(customers_router)

    return app


# Instância padrão para `uvicorn openops_api.main:app`. Usa banco em
# arquivo (não :memory:) para persistir entre reinicializações locais.
app = create_app(db_path="openops.db")
