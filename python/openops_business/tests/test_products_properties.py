"""
Testes baseados em propriedades do módulo de Produtos. O Hypothesis vai
tentar ativamente encontrar combinações de nome/preço/estoque que
deveriam ser rejeitadas mas não são (ou vice-versa) — é exatamente o
tipo de bug de validação que testes manuais tendem a deixar passar.
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from openops_business.products.models import Product
from openops_core.errors import ValidationError

valid_names = st.text(min_size=1, max_size=100).filter(lambda s: s.strip() != "")
valid_prices = st.floats(min_value=0.01, max_value=1_000_000, allow_nan=False, allow_infinity=False)
valid_stocks = st.integers(min_value=0, max_value=1_000_000)


@given(name=valid_names, price=valid_prices, stock=valid_stocks)
def test_any_valid_combination_is_accepted(name, price, stock):
    """Para QUALQUER combinação de nome não-vazio, preço positivo e
    estoque não-negativo, a criação do produto nunca é rejeitada — a
    validação não deve ser mais restritiva do que o documentado.
    """
    product = Product(name=name, price=price, stock=stock)

    assert product.name == name
    assert product.price == price
    assert product.stock == stock


@given(price=valid_prices, stock=valid_stocks)
def test_blank_or_empty_name_is_always_rejected(price, stock):
    """Para QUALQUER preço/estoque válidos, um nome vazio ou só com
    espaços é SEMPRE rejeitado — não importa o resto dos dados.
    """
    for blank in ("", "   ", "\t\n"):
        with pytest.raises(ValidationError):
            Product(name=blank, price=price, stock=stock)


@given(
    name=valid_names,
    price=st.floats(max_value=0, allow_nan=False, allow_infinity=False),
    stock=valid_stocks,
)
def test_non_positive_price_is_always_rejected(name, price, stock):
    """Para QUALQUER preço menor ou igual a zero, a criação é sempre
    rejeitada, não importa o nome ou o estoque.
    """
    with pytest.raises(ValidationError):
        Product(name=name, price=price, stock=stock)


@given(name=valid_names, price=valid_prices, negative_stock=st.integers(max_value=-1))
def test_negative_stock_is_always_rejected(name, price, negative_stock):
    """Para QUALQUER estoque negativo, a criação é sempre rejeitada."""
    with pytest.raises(ValidationError):
        Product(name=name, price=price, stock=negative_stock)


@given(name=valid_names, price=valid_prices, stock=valid_stocks, new_price=valid_prices)
def test_with_updates_never_changes_identity_fields(name, price, stock, new_price):
    """Para QUALQUER produto e QUALQUER atualização de preço, o id e o
    created_at nunca mudam — with_updates só deve tocar nos campos
    explicitamente passados, nunca na identidade do registro.
    """
    original = Product(name=name, price=price, stock=stock, id=1)

    updated = original.with_updates(price=new_price)

    assert updated.id == original.id
    assert updated.created_at == original.created_at
    assert updated.name == original.name  # não foi tocado
    assert updated.price == new_price
