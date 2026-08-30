import pytest

from openops_core.db import Database
from openops_core.registry import ModuleRegistry
from openops_business.customers.service import CustomerService, register, MODULE_INFO


@pytest.fixture
def service() -> CustomerService:
    return CustomerService(Database(":memory:"))


def test_create_and_get_roundtrip(service):
    created = service.create_customer(name="Sofia", email="sofia@exemplo.com")

    fetched = service.get_customer(created.id)

    assert fetched.name == "Sofia"


def test_update_partial_fields_only(service):
    created = service.create_customer(name="Bruno", phone="111")

    updated = service.update_customer(created.id, phone="222")

    assert updated.phone == "222"
    assert updated.name == "Bruno"  # preservado


def test_register_adds_module_info():
    registry = ModuleRegistry()

    register(registry)

    assert registry.get("customers") == MODULE_INFO
