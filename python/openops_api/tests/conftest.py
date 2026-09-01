"""
Fixtures compartilhadas dos testes de API. O `client` já vem
autenticado como um usuário "admin" (o primeiro usuário registrado em
cada app de teste sempre vira admin — ver `AuthService.register`), pois
a maioria dos testes de negócio não está testando autenticação em si,
só quer chamar a API normalmente. Os testes que exercitam autenticação
e RBAC de verdade estão em `test_auth_api.py` e usam `create_app`/
`TestClient` diretamente, sem este fixture.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from openops_core.registry import ModuleRegistry
from openops_api.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app(db_path=":memory:", registry=ModuleRegistry(), jwt_secret="segredo-de-teste-com-pelo-menos-32-bytes-de-comprimento")  # secscan:ignore (chave falsa de teste)

    bootstrap = TestClient(app)
    bootstrap.post("/auth/register", json={"username": "admin", "password": "senha-de-teste-123"})
    login = bootstrap.post("/auth/login", json={"username": "admin", "password": "senha-de-teste-123"})
    token = login.json()["access_token"]

    return TestClient(app, headers={"Authorization": f"Bearer {token}"})
