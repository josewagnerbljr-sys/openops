"""Testes de propriedade para apply_movement — a função mais crítica do
módulo (é ela que decide se uma saída de estoque é permitida).
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from openops_business.inventory.models import apply_movement
from openops_core.errors import ValidationError

non_negative_stock = st.integers(min_value=0, max_value=1_000_000)
positive_quantity = st.integers(min_value=1, max_value=1_000_000)


@given(stock=non_negative_stock, qty=positive_quantity)
def test_in_never_decreases_stock(stock, qty):
    """Para QUALQUER estoque e QUALQUER quantidade, uma entrada nunca
    resulta em um estoque menor que o original.
    """
    assert apply_movement(stock, "in", qty) >= stock


@given(stock=non_negative_stock, qty=positive_quantity)
def test_out_never_produces_negative_stock(stock, qty):
    """Para QUALQUER combinação, uma saída bem-sucedida (que não levanta
    erro) NUNCA resulta em estoque negativo — e quando levantaria
    estoque negativo, sempre levanta ValidationError em vez disso.
    """
    if qty > stock:
        with pytest.raises(ValidationError):
            apply_movement(stock, "out", qty)
    else:
        result = apply_movement(stock, "out", qty)
        assert result >= 0
        assert result == stock - qty


@given(stock=non_negative_stock, qty=non_negative_stock)
def test_adjustment_always_sets_exact_value(stock, qty):
    """Para QUALQUER estoque atual, um ajuste sempre resulta EXATAMENTE
    no valor informado — nunca soma, nunca subtrai.
    """
    assert apply_movement(stock, "adjustment", qty) == qty


@given(stock=non_negative_stock, qty=positive_quantity)
def test_in_then_out_same_quantity_returns_to_original(stock, qty):
    """Propriedade de ida-e-volta: aplicar uma entrada de N seguida de
    uma saída de N sempre retorna ao estoque original — nenhuma
    quantidade "se perde" no meio do caminho.
    """
    after_in = apply_movement(stock, "in", qty)
    after_out = apply_movement(after_in, "out", qty)

    assert after_out == stock
