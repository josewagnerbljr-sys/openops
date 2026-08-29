import pytest

from openops_core.registry import ModuleRegistry, ModuleInfo, register_module
from openops_core.errors import ConflictError, NotFoundError, ValidationError


def test_register_and_get():
    registry = ModuleRegistry()
    info = ModuleInfo(name="inventory", version="0.1.0", category="business")

    registry.register(info)

    assert registry.get("inventory") == info
    assert "inventory" in registry
    assert len(registry) == 1


def test_register_duplicate_name_raises_conflict():
    registry = ModuleRegistry()
    registry.register(ModuleInfo(name="sop", version="0.1.0", category="sop"))

    with pytest.raises(ConflictError):
        registry.register(ModuleInfo(name="sop", version="0.2.0", category="sop"))


def test_get_unknown_module_raises_not_found():
    registry = ModuleRegistry()

    with pytest.raises(NotFoundError):
        registry.get("nao-existe")


def test_unregister_removes_module():
    registry = ModuleRegistry()
    registry.register(ModuleInfo(name="finance", version="0.1.0", category="business"))

    registry.unregister("finance")

    assert "finance" not in registry


def test_unregister_unknown_raises_not_found():
    registry = ModuleRegistry()

    with pytest.raises(NotFoundError):
        registry.unregister("fantasma")


def test_list_filters_by_category():
    registry = ModuleRegistry()
    registry.register(ModuleInfo(name="inventory", version="0.1.0", category="business"))
    registry.register(ModuleInfo(name="sop-core", version="0.1.0", category="sop"))
    registry.register(ModuleInfo(name="sales", version="0.1.0", category="business"))

    business_modules = registry.list(category="business")

    assert [m.name for m in business_modules] == ["inventory", "sales"]


def test_invalid_category_raises_validation_error():
    with pytest.raises(ValidationError):
        ModuleInfo(name="x", version="0.1.0", category="categoria-invalida")


def test_empty_name_raises_validation_error():
    with pytest.raises(ValidationError):
        ModuleInfo(name="   ", version="0.1.0")


def test_register_module_decorator_registers_and_returns_target():
    registry = ModuleRegistry()

    @register_module(name="pricing", version="0.1.0", category="business", registry=registry)
    class PricingModule:
        pass

    assert "pricing" in registry
    assert PricingModule.__name__ == "PricingModule"


def test_clear_empties_registry():
    registry = ModuleRegistry()
    registry.register(ModuleInfo(name="x", version="0.1.0"))

    registry.clear()

    assert len(registry) == 0
