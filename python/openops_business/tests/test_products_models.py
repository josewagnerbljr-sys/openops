import pytest

from openops_business.products.models import Product
from openops_core.errors import ValidationError


def test_valid_product_is_created():
    product = Product(name="Café Especial", price=24.90, stock=10, category="bebidas")

    assert product.name == "Café Especial"
    assert product.id is None


@pytest.mark.parametrize(
    "kwargs,bad_field",
    [
        ({"name": "", "price": 10}, "name"),
        ({"name": "   ", "price": 10}, "name"),
        ({"name": "X", "price": 0}, "price"),
        ({"name": "X", "price": -5}, "price"),
        ({"name": "X", "price": 10, "stock": -1}, "stock"),
    ],
)
def test_invalid_product_raises_validation_error(kwargs, bad_field):
    with pytest.raises(ValidationError) as exc_info:
        Product(**kwargs)

    assert bad_field in exc_info.value.details


def test_with_updates_preserves_id_and_created_at():
    original = Product(name="Água", price=5.0, id=1)

    updated = original.with_updates(price=6.0)

    assert updated.id == 1
    assert updated.price == 6.0
    assert updated.name == "Água"  # não alterado, preservado
    assert updated.updated_at is not None


def test_with_updates_validates_new_values():
    original = Product(name="Água", price=5.0)

    with pytest.raises(ValidationError):
        original.with_updates(price=-1)
