import pytest
from fastapi.testclient import TestClient


def test_root_lists_both_modules(client):
    response = client.get("/")

    modules = response.json()["modules"]
    assert "products" in modules
    assert "customers" in modules


def test_create_customer_returns_201(client):
    response = client.post("/customers", json={"name": "Helena", "email": "helena@exemplo.com"})

    assert response.status_code == 201
    assert response.json()["name"] == "Helena"


def test_create_invalid_email_returns_422(client):
    response = client.post("/customers", json={"name": "X", "email": "invalido"})

    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


def test_duplicate_email_returns_409(client):
    client.post("/customers", json={"name": "A", "email": "dup@exemplo.com"})

    response = client.post("/customers", json={"name": "B", "email": "dup@exemplo.com"})

    assert response.status_code == 409


def test_full_crud_lifecycle(client):
    create_resp = client.post("/customers", json={"name": "Rafael"})
    customer_id = create_resp.json()["id"]

    get_resp = client.get(f"/customers/{customer_id}")
    assert get_resp.json()["name"] == "Rafael"

    update_resp = client.put(f"/customers/{customer_id}", json={"phone": "4499990000"})
    assert update_resp.json()["phone"] == "4499990000"

    delete_resp = client.delete(f"/customers/{customer_id}")
    assert delete_resp.status_code == 204

    assert client.get(f"/customers/{customer_id}").status_code == 404


def test_search_filters_results(client):
    client.post("/customers", json={"name": "Ana Paula"})
    client.post("/customers", json={"name": "Carlos"})

    response = client.get("/customers", params={"search": "Ana"})

    names = [c["name"] for c in response.json()]
    assert names == ["Ana Paula"]
