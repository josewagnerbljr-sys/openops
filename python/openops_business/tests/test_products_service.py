import pytest

from openops_core.db import Database
from openops_core.registry import ModuleRegistry
from openops_core.errors import NotFoundError
from openops_business.products.service import ProductService, register, MODULE_INFO


@pytest.fixture
def service() -> ProductService:
    return ProductService(Database(":memory:"))


def test_migrations_applied_on_init(service):
    # se as migrations não tivessem rodado, isso levantaria um erro de SQL
    assert service.list_products() == []


def test_create_and_get_roundtrip(service):
    created = service.create_product(name="Torta de Limão", price=18.0, stock=3, category="doces")

    fetched = service.get_product(created.id)

    assert fetched.name == "Torta de Limão"
    assert fetched.stock == 3


def test_update_partial_fields_only(service):
    created = service.create_product(name="Refrigerante", price=6.0, stock=20)

    updated = service.update_product(created.id, price=6.5)

    assert updated.price == 6.5
    assert updated.stock == 20  # não foi tocado, preservado
    assert updated.name == "Refrigerante"


def test_delete_product(service):
    created = service.create_product(name="Temporário", price=1.0)

    service.delete_product(created.id)

    with pytest.raises(NotFoundError):
        service.get_product(created.id)


def test_register_adds_module_info_to_registry():
    registry = ModuleRegistry()

    register(registry)

    assert registry.get("products") == MODULE_INFO
    assert registry.get("products").category == "business"
