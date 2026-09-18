from datetime import date, timedelta

import pytest

from openops_core.db import Database
from openops_core.events import EventBus
from openops_business.products.service import ProductService
from openops_business.inventory.service import InventoryService


@pytest.fixture
def setup():
    db = Database(":memory:")
    products = ProductService(db)
    product = products.create_product(name="Dipirona 500mg", price=8.5, stock=0, category="farmacia")
    events = EventBus()
    inventory = InventoryService(db, products, event_bus=events)
    return inventory, products, events, product


def test_register_movement_persists_batch_and_expiry(setup):
    inventory, _, _, product = setup
    expiry = date.today() + timedelta(days=10)

    movement = inventory.register_movement(
        product_id=product.id,
        movement_type="in",
        quantity=100,
        batch_number="LOTE-2026-09",
        expiry_date=expiry,
    )

    assert movement.batch_number == "LOTE-2026-09"
    assert movement.expiry_date == expiry


def test_movement_without_batch_or_expiry_keeps_backward_compatible_defaults(setup):
    inventory, _, _, product = setup

    movement = inventory.register_movement(product_id=product.id, movement_type="in", quantity=10)

    assert movement.batch_number == ""
    assert movement.expiry_date is None


def test_check_expiring_batches_finds_batch_within_window(setup):
    inventory, _, events, product = setup
    alerts = []
    events.subscribe("stock.expiring_soon", lambda event: alerts.append(event.payload))

    expiry = date.today() + timedelta(days=5)
    inventory.register_movement(
        product_id=product.id,
        movement_type="in",
        quantity=50,
        batch_number="LOTE-VENCE-LOGO",
        expiry_date=expiry,
    )

    found = inventory.check_expiring_batches(within_days=30)

    assert len(found) == 1
    assert found[0].batch_number == "LOTE-VENCE-LOGO"
    assert len(alerts) == 1
    assert alerts[0]["batch_number"] == "LOTE-VENCE-LOGO"
    assert alerts[0]["days_remaining"] == 5


def test_check_expiring_batches_ignores_batches_outside_window(setup):
    inventory, _, _, product = setup

    far_expiry = date.today() + timedelta(days=200)
    inventory.register_movement(
        product_id=product.id,
        movement_type="in",
        quantity=50,
        batch_number="LOTE-LONGE",
        expiry_date=far_expiry,
    )

    found = inventory.check_expiring_batches(within_days=30)

    assert found == []


def test_check_expiring_batches_ignores_movements_without_expiry(setup):
    inventory, _, _, product = setup

    inventory.register_movement(product_id=product.id, movement_type="in", quantity=50)

    found = inventory.check_expiring_batches(within_days=30)

    assert found == []


def test_check_expiring_batches_orders_by_expiry_ascending_fefo(setup):
    inventory, products, _, product = setup
    other = products.create_product(name="Paracetamol 750mg", price=6.0, stock=0, category="farmacia")

    inventory.register_movement(
        product_id=product.id,
        movement_type="in",
        quantity=10,
        batch_number="VENCE-EM-20",
        expiry_date=date.today() + timedelta(days=20),
    )
    inventory.register_movement(
        product_id=other.id,
        movement_type="in",
        quantity=10,
        batch_number="VENCE-EM-3",
        expiry_date=date.today() + timedelta(days=3),
    )

    found = inventory.check_expiring_batches(within_days=30)

    assert [m.batch_number for m in found] == ["VENCE-EM-3", "VENCE-EM-20"]
