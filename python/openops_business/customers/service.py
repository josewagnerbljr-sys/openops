"""
openops_business.customers.service
===================================

Fachada de negócio do módulo de Clientes — mesmo padrão de
`products.service`.
"""

from __future__ import annotations

from openops_core.db import Database
from openops_core.registry import ModuleInfo, default_registry

from .models import Customer
from .repository import CustomerRepository, CUSTOMERS_MIGRATIONS

MODULE_INFO = ModuleInfo(
    name="customers",
    version="0.1.0",
    category="business",
    description="Cadastro de clientes do Business OS",
)


class CustomerService:
    def __init__(self, db: Database) -> None:
        self._db = db
        self._db.migrate(CUSTOMERS_MIGRATIONS)
        self._repository = CustomerRepository(db)

    def create_customer(
        self,
        *,
        name: str,
        email: str | None = None,
        phone: str | None = None,
        document: str | None = None,
    ) -> Customer:
        customer = Customer(name=name, email=email, phone=phone, document=document)
        return self._repository.create(customer)

    def get_customer(self, customer_id: int) -> Customer:
        return self._repository.get(customer_id)

    def list_customers(self, *, search: str | None = None) -> list[Customer]:
        return self._repository.list(search=search)

    def update_customer(
        self,
        customer_id: int,
        *,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        document: str | None = None,
    ) -> Customer:
        current = self._repository.get(customer_id)
        updated = current.with_updates(
            **{
                k: v
                for k, v in {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "document": document,
                }.items()
                if v is not None
            }
        )
        return self._repository.update(customer_id, updated)

    def delete_customer(self, customer_id: int) -> None:
        self._repository.delete(customer_id)


def register(registry=None) -> None:
    (registry if registry is not None else default_registry).register(MODULE_INFO)
