import pytest

from openops_business.inventory.models import StockMovement, apply_movement
from openops_core.errors import ValidationError


def test_valid_movement_is_created():
    movement = StockMovement(product_id=1, movement_type="in", quantity=10)

    assert movement.movement_type == "in"


def test_invalid_movement_type_is_rejected():
    with pytest.raises(ValidationError) as exc_info:
        StockMovement(product_id=1, movement_type="teleport", quantity=5)

    assert "movement_type" in exc_info.value.details


def test_negative_quantity_is_rejected():
    with pytest.raises(ValidationError):
        StockMovement(product_id=1, movement_type="in", quantity=-1)


def test_apply_movement_in_increases_stock():
    assert apply_movement(10, "in", 5) == 15


def test_apply_movement_out_decreases_stock():
    assert apply_movement(10, "out", 3) == 7


def test_apply_movement_out_exceeding_stock_raises():
    with pytest.raises(ValidationError) as exc_info:
        apply_movement(current_stock=5, movement_type="out", quantity=10)

    assert exc_info.value.details["estoque_atual"] == 5
    assert exc_info.value.details["quantidade_solicitada"] == 10


def test_apply_movement_adjustment_sets_absolute_value():
    assert apply_movement(current_stock=999, movement_type="adjustment", quantity=42) == 42


def test_apply_movement_out_exactly_zeroing_stock_is_allowed():
    assert apply_movement(current_stock=5, movement_type="out", quantity=5) == 0


def test_apply_movement_unknown_type_raises():
    with pytest.raises(ValidationError):
        apply_movement(10, "invalido", 1)
