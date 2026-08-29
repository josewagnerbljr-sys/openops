"""
openops_business.products.service
==================================

Fachada de negócio do módulo de Produtos. É o que a API (e qualquer
outro consumidor — CLI futura, outro módulo de negócio) deve usar; nunca
o repositório diretamente. Também é aqui que o módulo se registra no
``ModuleRegistry`` do core, tornando-se descobrível.
"""

from __future__ import annotations

from openops_core.db import Database
from openops_core.registry import ModuleInfo, default_registry

from .models import Product
from .repository import ProductRepository, PRODUCTS_MIGRATIONS

MODULE_INFO = ModuleInfo(
    name="products",
    version="0.1.0",
    category="business",
    description="Cadastro de produtos do Business OS",
)


class ProductService:
    """Ponto de entrada único do módulo de Produtos.

    Aplica as migrations do módulo na inicialização (idempotente — pode
    ser chamado toda vez que o serviço sobe, sem risco de reaplicar).
    """

    def __init__(self, db: Database) -> None:
        self._db = db
        self._db.migrate(PRODUCTS_MIGRATIONS)
        self._repository = ProductRepository(db)

    def create_product(self, *, name: str, price: float, stock: int = 0, category: str = "") -> Product:
        product = Product(name=name, price=price, stock=stock, category=category)
        return self._repository.create(product)

    def get_product(self, product_id: int) -> Product:
        return self._repository.get(product_id)

    def list_products(self, *, category: str | None = None) -> list[Product]:
        return self._repository.list(category=category)

    def update_product(
        self,
        product_id: int,
        *,
        name: str | None = None,
        price: float | None = None,
        stock: int | None = None,
        category: str | None = None,
    ) -> Product:
        current = self._repository.get(product_id)
        updated = current.with_updates(
            **{
                k: v
                for k, v in {"name": name, "price": price, "stock": stock, "category": category}.items()
                if v is not None
            }
        )
        return self._repository.update(product_id, updated)

    def delete_product(self, product_id: int) -> None:
        self._repository.delete(product_id)


def register(registry=None) -> None:
    """Registra o módulo de Produtos no registry (padrão ou o informado).
    Seguro para chamar mais de uma vez apenas se registries diferentes
    forem usados — o mesmo registry rejeita registro duplicado por
    design (ver ``openops_core.registry``).
    """
    (registry if registry is not None else default_registry).register(MODULE_INFO)
