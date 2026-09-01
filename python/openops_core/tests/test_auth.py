import time

import pytest

from openops_core.db import Database
from openops_core.auth import AuthService, role_satisfies
from openops_core.errors import AuthorizationError, ConflictError, ValidationError

SECRET = "chave-de-teste-bem-longa-o-suficiente"  # secscan:ignore (chave falsa de teste)


@pytest.fixture
def auth() -> AuthService:
    return AuthService(Database(":memory:"), secret_key=SECRET, token_ttl_seconds=3600)  # secscan:ignore


def test_first_registered_user_becomes_admin(auth):
    user = auth.register(username="jose", password="senha12345", role="viewer")

    assert user.role == "admin"  # ignorou o "viewer" pedido, é o primeiro usuário


def test_second_user_gets_requested_role(auth):
    auth.register(username="jose", password="senha12345")
    second = auth.register(username="maria", password="outrasenha", role="operator")

    assert second.role == "operator"


def test_duplicate_username_raises_conflict(auth):
    auth.register(username="jose", password="senha12345")

    with pytest.raises(ConflictError):
        auth.register(username="jose", password="outrasenha")


def test_short_password_is_rejected(auth):
    with pytest.raises(ValidationError):
        auth.register(username="jose", password="123")


def test_invalid_role_is_rejected(auth):
    with pytest.raises(ValidationError):
        auth.register(username="jose", password="senha12345", role="super-root")


def test_authenticate_with_correct_password_returns_token(auth):
    auth.register(username="jose", password="senha-correta-123")

    token = auth.authenticate(username="jose", password="senha-correta-123")

    assert isinstance(token, str) and len(token) > 20


def test_authenticate_with_wrong_password_raises(auth):
    auth.register(username="jose", password="senha-correta-123")

    with pytest.raises(AuthorizationError):
        auth.authenticate(username="jose", password="senha-errada")


def test_authenticate_with_unknown_user_raises(auth):
    with pytest.raises(AuthorizationError):
        auth.authenticate(username="fantasma", password="qualquer")


def test_decode_token_roundtrip(auth):
    auth.register(username="jose", password="senha-correta-123")
    token = auth.authenticate(username="jose", password="senha-correta-123")

    payload = auth.decode_token(token)

    assert payload.username == "jose"
    assert payload.role == "admin"


def test_decode_expired_token_raises():
    db = Database(":memory:")
    auth = AuthService(db, secret_key=SECRET, token_ttl_seconds=1)  # secscan:ignore
    auth.register(username="jose", password="senha-correta-123")
    token = auth.authenticate(username="jose", password="senha-correta-123")

    time.sleep(1.2)

    with pytest.raises(AuthorizationError):
        auth.decode_token(token)


def test_decode_garbage_token_raises(auth):
    with pytest.raises(AuthorizationError):
        auth.decode_token("isso-nao-e-um-jwt-valido")


def test_decode_token_signed_with_different_secret_raises(auth):
    auth.register(username="jose", password="senha-correta-123")
    token = auth.authenticate(username="jose", password="senha-correta-123")

    forged_auth = AuthService(Database(":memory:"), secret_key="outra-chave-completamente-diferente-123")  # secscan:ignore (chave falsa de teste)

    with pytest.raises(AuthorizationError):
        forged_auth.decode_token(token)


def test_weak_secret_key_is_rejected():
    with pytest.raises(ValidationError):
        AuthService(Database(":memory:"), secret_key="curta")  # secscan:ignore (chave falsa, propositalmente fraca, para testar rejeição)


@pytest.mark.parametrize(
    "user_role,minimum,expected",
    [
        ("admin", "viewer", True),
        ("admin", "operator", True),
        ("admin", "admin", True),
        ("operator", "viewer", True),
        ("operator", "operator", True),
        ("operator", "admin", False),
        ("viewer", "viewer", True),
        ("viewer", "operator", False),
        ("viewer", "admin", False),
    ],
)
def test_role_satisfies_matrix(user_role, minimum, expected):
    assert role_satisfies(user_role, minimum) is expected
