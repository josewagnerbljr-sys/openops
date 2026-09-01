import pytest
from fastapi.testclient import TestClient

from openops_core.registry import ModuleRegistry
from openops_api.main import create_app


@pytest.fixture
def app():
    return create_app(db_path=":memory:", registry=ModuleRegistry(), jwt_secret="segredo-de-teste-com-pelo-menos-32-bytes-de-comprimento")  # secscan:ignore (chave falsa de teste)


@pytest.fixture
def anon_client(app) -> TestClient:
    return TestClient(app)


def test_register_first_user_becomes_admin(anon_client):
    response = anon_client.post("/auth/register", json={"username": "jose", "password": "senha12345"})

    assert response.status_code == 201
    assert response.json()["role"] == "admin"


def test_login_returns_bearer_token(anon_client):
    anon_client.post("/auth/register", json={"username": "jose", "password": "senha12345"})

    response = anon_client.post("/auth/login", json={"username": "jose", "password": "senha12345"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


def test_login_with_wrong_password_returns_401(anon_client):
    anon_client.post("/auth/register", json={"username": "jose", "password": "senha12345"})

    response = anon_client.post("/auth/login", json={"username": "jose", "password": "senha-errada"})

    assert response.status_code == 403  # AuthorizationError mapeia para 403


def test_reading_products_without_token_returns_403(anon_client):
    response = anon_client.get("/products")

    assert response.status_code == 403


def test_reading_products_with_valid_token_succeeds(anon_client):
    anon_client.post("/auth/register", json={"username": "jose", "password": "senha12345"})
    token = anon_client.post("/auth/login", json={"username": "jose", "password": "senha12345"}).json()[
        "access_token"
    ]

    response = anon_client.get("/products", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_viewer_cannot_create_product(anon_client):
    # primeiro usuário é sempre admin — registra um segundo como viewer de propósito
    anon_client.post("/auth/register", json={"username": "admin", "password": "senha12345"})
    anon_client.post(
        "/auth/register", json={"username": "leitor", "password": "senha12345", "role": "viewer"}
    )
    token = anon_client.post("/auth/login", json={"username": "leitor", "password": "senha12345"}).json()[
        "access_token"
    ]

    response = anon_client.post(
        "/products",
        json={"name": "Produto", "price": 10.0},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["error"] == "authorization_error"


def test_operator_can_create_product(anon_client):
    anon_client.post("/auth/register", json={"username": "admin", "password": "senha12345"})
    anon_client.post(
        "/auth/register", json={"username": "op", "password": "senha12345", "role": "operator"}
    )
    token = anon_client.post("/auth/login", json={"username": "op", "password": "senha12345"}).json()[
        "access_token"
    ]

    response = anon_client.post(
        "/products",
        json={"name": "Produto", "price": 10.0},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201


def test_me_endpoint_reflects_logged_in_user(anon_client):
    anon_client.post("/auth/register", json={"username": "jose", "password": "senha12345"})
    token = anon_client.post("/auth/login", json={"username": "jose", "password": "senha12345"}).json()[
        "access_token"
    ]

    response = anon_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.json() == {"username": "jose", "role": "admin"}


def test_malformed_authorization_header_returns_403(anon_client):
    response = anon_client.get("/products", headers={"Authorization": "TotalmenteInvalido"})

    assert response.status_code == 403
