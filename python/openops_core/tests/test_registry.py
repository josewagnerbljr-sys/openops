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

    with pytest.raises(ConflictError) as exc_info:
        registry.register(ModuleInfo(name="sop", version="0.2.0", category="sop"))

    assert "sop" in exc_info.value.message
    assert exc_info.value.details == {"existing_version": "0.1.0"}


def test_get_unknown_module_raises_not_found():
    registry = ModuleRegistry()

    with pytest.raises(NotFoundError) as exc_info:
        registry.get("nao-existe")

    assert "nao-existe" in exc_info.value.message


def test_unregister_removes_module():
    registry = ModuleRegistry()
    registry.register(ModuleInfo(name="finance", version="0.1.0", category="business"))

    registry.unregister("finance")

    assert "finance" not in registry


def test_unregister_unknown_raises_not_found():
    registry = ModuleRegistry()

    with pytest.raises(NotFoundError) as exc_info:
        registry.unregister("fantasma")

    assert "fantasma" in exc_info.value.message


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


def test_register_module_decorator_uses_core_as_default_category():
    registry = ModuleRegistry()

    @register_module(name="untyped", version="0.1.0", registry=registry)
    class UntypedModule:
        pass

    info = registry.get("untyped")
    assert info.category == "core"
    assert info.description == ""


def test_register_module_decorator_stores_all_fields_and_metadata():
    registry = ModuleRegistry()

    @register_module(
        name="pricing",
        version="1.2.3",
        category="business",
        description="Cálculo de preços e margens",
        registry=registry,
        author="José",
        license="Apache-2.0",
    )
    class PricingModule:
        pass

    info = registry.get("pricing")
    assert info.version == "1.2.3"
    assert info.category == "business"
    assert info.description == "Cálculo de preços e margens"
    assert info.metadata == {"author": "José", "license": "Apache-2.0"}


def test_clear_empties_registry():
    registry = ModuleRegistry()
    registry.register(ModuleInfo(name="x", version="0.1.0"))

    registry.clear()

    assert len(registry) == 0
