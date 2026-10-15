# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""Remoção segura de produtos: apaga sem histórico, arquiva com histórico."""

import pytest

from openops_core.db import Database
from openops_core.errors import ConflictError, NotFoundError
from openops_business.inventory.service import InventoryService
from openops_business.products.service import ProductService


@pytest.fixture
def services():
    db = Database(":memory:")
    products = ProductService(db)
    return products, InventoryService(db, products)


def test_remove_without_history_deletes(services):
    products, _ = services
    p = products.create_product(name="A", price=1.0)

    assert products.remove_product(p.id) == "deleted"
    with pytest.raises(NotFoundError):
        products.get_product(p.id)


def test_remove_with_history_archives(services):
    products, inventory = services
    p = products.create_product(name="A", price=1.0, stock=0)
    inventory.register_movement(product_id=p.id, movement_type="in", quantity=5)

    assert products.remove_product(p.id) == "archived"
    assert products.list_products() == []
    assert len(inventory.list_movements(product_id=p.id)) == 1   # histórico preservado
    assert products.get_product(p.id).stock == 0                  # ainda consultável por id


def test_archived_name_can_be_reused(services):
    products, inventory = services
    p = products.create_product(name="A", price=1.0)
    inventory.register_movement(product_id=p.id, movement_type="in", quantity=1)
    products.remove_product(p.id)

    assert products.create_product(name="A", price=2.0).id != p.id


def test_plain_delete_with_history_is_a_clear_conflict_not_a_crash(services):
    products, inventory = services
    p = products.create_product(name="A", price=1.0)
    inventory.register_movement(product_id=p.id, movement_type="in", quantity=1)

    with pytest.raises(ConflictError):
        products.delete_product(p.id)


def test_failed_movement_leaves_stock_and_history_untouched(services):
    products, inventory = services
    p = products.create_product(name="A", price=1.0, stock=3)

    with pytest.raises(Exception):
        inventory.register_movement(product_id=p.id, movement_type="out", quantity=9)

    assert products.get_product(p.id).stock == 3
    assert inventory.list_movements() == []
