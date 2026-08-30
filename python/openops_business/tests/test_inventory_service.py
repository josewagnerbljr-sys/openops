import pytest

from openops_core.db import Database
from openops_core.events import EventBus
from openops_core.errors import NotFoundError, ValidationError
from openops_business.products.service import ProductService
from openops_business.inventory.service import InventoryService, LOW_STOCK_THRESHOLD


@pytest.fixture
def setup():
    db = Database(":memory:")
    products = ProductService(db)
    product = products.create_product(name="Caneca", price=15.0, stock=20)
    events = EventBus()
    inventory = InventoryService(db, products, event_bus=events)
    return inventory, products, events, product


def test_in_movement_increases_product_stock(setup):
    inventory, products, _, product = setup

    inventory.register_movement(product_id=product.id, movement_type="in", quantity=10)

    assert products.get_product(product.id).stock == 30


def test_out_movement_decreases_product_stock(setup):
    inventory, products, _, product = setup

    inventory.register_movement(product_id=product.id, movement_type="out", quantity=5)

    assert products.get_product(product.id).stock == 15


def test_out_movement_exceeding_stock_raises_and_does_not_persist(setup):
    inventory, products, _, product = setup

    with pytest.raises(ValidationError):
        inventory.register_movement(product_id=product.id, movement_type="out", quantity=999)

    # nem o produto nem o histórico devem ter sido alterados
    assert products.get_product(product.id).stock == 20
    assert inventory.list_movements(product_id=product.id) == []


def test_movement_for_unknown_product_raises_not_found(setup):
    inventory, _, _, _ = setup

    with pytest.raises(NotFoundError):
        inventory.register_movement(product_id=999999, movement_type="in", quantity=1)


def test_stock_changed_event_is_published(setup):
    inventory, _, events, product = setup
    received = []
    events.subscribe("stock.changed", lambda event: received.append(event.payload))

    inventory.register_movement(product_id=product.id, movement_type="in", quantity=5)

    assert len(received) == 1
    assert received[0]["new_stock"] == 25
    assert received[0]["product_id"] == product.id


def test_stock_low_event_fires_when_crossing_threshold(setup):
    inventory, _, events, product = setup
    low_stock_alerts = []
    events.subscribe("stock.low", lambda event: low_stock_alerts.append(event.payload))

    # produto começa com 20; tira o suficiente para cruzar o threshold (5)
    inventory.register_movement(
        product_id=product.id, movement_type="out", quantity=20 - LOW_STOCK_THRESHOLD
    )

    assert len(low_stock_alerts) == 1
    assert low_stock_alerts[0]["stock"] == LOW_STOCK_THRESHOLD


def test_stock_low_event_does_not_fire_when_stock_is_healthy(setup):
    inventory, _, events, product = setup
    low_stock_alerts = []
    events.subscribe("stock.low", lambda event: low_stock_alerts.append(event.payload))

    inventory.register_movement(product_id=product.id, movement_type="out", quantity=2)

    assert low_stock_alerts == []


def test_current_stock_reflects_product(setup):
    inventory, _, _, product = setup

    assert inventory.current_stock(product.id) == 20
