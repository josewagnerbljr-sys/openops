import pytest
from fastapi.testclient import TestClient

from openops_core.registry import ModuleRegistry
from openops_api.main import create_app


@pytest.fixture
def client() -> TestClient:
    # cada teste recebe app + banco + registry isolados — nenhum estado
    # vaza de um teste para o outro
    app = create_app(db_path=":memory:", registry=ModuleRegistry())
    return TestClient(app)


def test_root_lists_registered_modules(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "products" in response.json()["modules"]


def test_create_product_returns_201(client):
    response = client.post(
        "/products", json={"name": "Espresso", "price": 7.5, "stock": 50, "category": "bebidas"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Espresso"
    assert body["id"] is not None


def test_create_invalid_product_returns_422(client):
    response = client.post("/products", json={"name": "", "price": -1})

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"
    assert "name" in body["details"]
    assert "price" in body["details"]


def test_get_unknown_product_returns_404(client):
    response = client.get("/products/999")

    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_full_crud_lifecycle(client):
    create_resp = client.post("/products", json={"name": "Capuccino", "price": 9.0})
    product_id = create_resp.json()["id"]

    get_resp = client.get(f"/products/{product_id}")
    assert get_resp.json()["name"] == "Capuccino"

    update_resp = client.put(f"/products/{product_id}", json={"price": 9.5})
    assert update_resp.status_code == 200
    assert update_resp.json()["price"] == 9.5

    list_resp = client.get("/products")
    assert any(p["id"] == product_id for p in list_resp.json())

    delete_resp = client.delete(f"/products/{product_id}")
    assert delete_resp.status_code == 204

    get_after_delete = client.get(f"/products/{product_id}")
    assert get_after_delete.status_code == 404


def test_duplicate_name_returns_409(client):
    client.post("/products", json={"name": "Único", "price": 1.0})

    response = client.post("/products", json={"name": "Único", "price": 2.0})

    assert response.status_code == 409
    assert response.json()["error"] == "conflict"


def test_list_filters_by_category(client):
    client.post("/products", json={"name": "Café", "price": 8.0, "category": "bebidas"})
    client.post("/products", json={"name": "Guardanapo", "price": 2.0, "category": "descartáveis"})

    response = client.get("/products", params={"category": "bebidas"})

    names = [p["name"] for p in response.json()]
    assert names == ["Café"]
