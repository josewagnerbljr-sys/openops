"""
openops_api.main
=================

Ponto de entrada da API HTTP do OpenOps (Fase 9 do roadmap, adiantada
junto com o Business OS). Além dos módulos de negócio, esta versão já
inclui:

- **Autenticação e RBAC** (`openops_api.auth`) — fecha o principal risco
  aceito documentado no THREAT_MODEL.md: leitura exige login, escrita
  exige papel "operator" ou superior.
- **Observabilidade** (`openops_api.observability`) — tracing distribuído
  via OpenTelemetry e métricas Prometheus em `/metrics`.

``create_app()`` é uma factory, não um singleton global — cada chamada
monta uma instância nova, com seu próprio banco. Isso é o que permite os
testes de API rodarem isolados uns dos outros sem nenhum estado
compartilhado escondido.
"""

from __future__ import annotations

import os
import secrets

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from openops_core.auth import AuthService
from openops_core.db import Database
from openops_core.errors import OpenOpsError, http_status_for
from openops_core.registry import ModuleRegistry, default_registry

from openops_api.auth import router as auth_router
from openops_api.observability import setup_tracing, setup_metrics

from openops_business.products import ProductService
from openops_business.products import router as products_router
from openops_business.products.service import register as register_products

from openops_business.customers import CustomerService
from openops_business.customers import router as customers_router
from openops_business.customers.service import register as register_customers

from openops_business.inventory import InventoryService
from openops_business.inventory import router as inventory_router
from openops_business.inventory.service import register as register_inventory


def create_app(
    *,
    db_path: str = ":memory:",
    registry: ModuleRegistry | None = None,
    jwt_secret: str | None = None,
) -> FastAPI:
    """Monta uma instância da API OpenOps.

    Args:
        db_path: caminho do arquivo SQLite, ou ``:memory:`` (padrão,
            usado em testes e demonstrações rápidas).
        registry: registry de módulos a usar; por padrão, o
            ``default_registry`` compartilhado do processo.
        jwt_secret: chave de assinatura dos tokens JWT. Se omitida, usa
            a variável de ambiente ``OPENOPS_JWT_SECRET``; se essa
            também não existir, gera uma chave aleatória por instância
            (adequado para testes/demos — **nunca** para produção real,
            onde a chave precisa ser fixa entre reinicializações, ou
            todo token emitido antes de reiniciar vira inválido).
    """

    app = FastAPI(
        title="OpenOps API",
        description="Open Source Business Operations Platform — API HTTP",
        version="0.1.0",
    )

    target_registry = registry if registry is not None else default_registry

    effective_secret = jwt_secret or os.environ.get("OPENOPS_JWT_SECRET") or secrets.token_hex(32)

    db = Database(db_path)
    auth_service = AuthService(db, secret_key=effective_secret)

    product_service = ProductService(db)
    if "products" not in target_registry:
        register_products(target_registry)

    customer_service = CustomerService(db)
    if "customers" not in target_registry:
        register_customers(target_registry)

    inventory_service = InventoryService(db, product_service)
    if "inventory" not in target_registry:
        register_inventory(target_registry)

    app.state.db = db
    app.state.auth_service = auth_service
    app.state.product_service = product_service
    app.state.customer_service = customer_service
    app.state.inventory_service = inventory_service
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

    app.include_router(auth_router)
    app.include_router(products_router)
    app.include_router(customers_router)
    app.include_router(inventory_router)

    setup_tracing(app)
    setup_metrics(app)

    return app


# Instância padrão para `uvicorn openops_api.main:app`. O caminho do
# banco é configurável via OPENOPS_DB_PATH — necessário para persistir
# dados corretamente quando rodando em um container Docker com volume
# montado (ver docker-compose.yml).
if os.environ.get("OPENOPS_TRACING_CONSOLE") == "1":
    from openops_api.observability import configure_console_export

    configure_console_export()

app = create_app(db_path=os.environ.get("OPENOPS_DB_PATH", "openops.db"))
