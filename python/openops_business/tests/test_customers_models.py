import pytest

from openops_business.customers.models import Customer
from openops_core.errors import ValidationError


def test_valid_customer_with_all_fields():
    customer = Customer(name="Maria Silva", email="maria@exemplo.com", phone="44999998888", document="12345678900")

    assert customer.name == "Maria Silva"
    assert customer.email == "maria@exemplo.com"


def test_customer_without_optional_fields():
    customer = Customer(name="Cliente Balcão")

    assert customer.email is None
    assert customer.phone is None
    assert customer.document is None


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_name_raises_validation_error(blank):
    with pytest.raises(ValidationError) as exc_info:
        Customer(name=blank)

    assert "name" in exc_info.value.details


@pytest.mark.parametrize(
    "bad_email",
    ["sem-arroba", "duplo@@arroba.com", "@semlocal.com", "semdominio@", "dominio@semponto", "@.com"],
)
def test_invalid_email_raises_validation_error(bad_email):
    with pytest.raises(ValidationError) as exc_info:
        Customer(name="X", email=bad_email)

    assert "email" in exc_info.value.details


def test_with_updates_preserves_id_and_created_at():
    original = Customer(name="Ana", email="ana@exemplo.com", id=7)

    updated = original.with_updates(phone="4499990000")

    assert updated.id == 7
    assert updated.phone == "4499990000"
    assert updated.email == "ana@exemplo.com"  # não tocado, preservado
