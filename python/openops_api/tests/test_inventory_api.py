import pytest
from fastapi.testclient import TestClient

from openops_core.registry import ModuleRegistry
from openops_api.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app(db_path=":memory:", registry=ModuleRegistry())
    return TestClient(app)


@pytest.fixture
def product_id(client) -> int:
    response = client.post("/products", json={"name": "Xícara", "price": 12.0, "stock": 10})
    return response.json()["id"]


def test_root_lists_all_three_modules(client):
    modules = client.get("/").json()["modules"]

    assert set(modules) == {"products", "customers", "inventory"}


def test_register_in_movement_updates_stock(client, product_id):
    response = client.post(
        "/inventory/movements",
        json={"product_id": product_id, "movement_type": "in", "quantity": 5, "reason": "reposição"},
    )

    assert response.status_code == 201

    stock_response = client.get(f"/inventory/products/{product_id}/stock")
    assert stock_response.json()["stock"] == 15


def test_out_movement_exceeding_stock_returns_422(client, product_id):
    response = client.post(
        "/inventory/movements",
        json={"product_id": product_id, "movement_type": "out", "quantity": 999},
    )

    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


def test_movement_for_unknown_product_returns_404(client):
    response = client.post(
        "/inventory/movements",
        json={"product_id": 999999, "movement_type": "in", "quantity": 1},
    )

    assert response.status_code == 404


def test_list_movements_filters_by_product(client, product_id):
    client.post("/inventory/movements", json={"product_id": product_id, "movement_type": "in", "quantity": 1})

    response = client.get("/inventory/movements", params={"product_id": product_id})

    assert len(response.json()) == 1
