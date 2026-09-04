import pytest
from fastapi.testclient import TestClient

from openops_core.registry import ModuleRegistry
from openops_api.main import create_app


@pytest.fixture
def client() -> TestClient:
    # público de propósito — nem sequer usa o conftest com auth
    app = create_app(db_path=":memory:", registry=ModuleRegistry(), jwt_secret="x" * 32)
    return TestClient(app)


def test_encrypt_endpoint_is_public(client):
    response = client.post("/security-demo/encrypt", json={"plaintext": "segredo de teste"})

    assert response.status_code == 200
    body = response.json()
    assert body["plaintext"] == "segredo de teste"
    assert len(bytes.fromhex(body["key_hex"])) == 32
    assert len(bytes.fromhex(body["nonce_hex"])) == 12


def test_encrypt_then_decrypt_roundtrip(client):
    encrypted = client.post("/security-demo/encrypt", json={"plaintext": "mensagem de verdade"}).json()

    decrypted = client.post(
        "/security-demo/decrypt",
        json={
            "key_hex": encrypted["key_hex"],
            "nonce_hex": encrypted["nonce_hex"],
            "ciphertext_hex": encrypted["ciphertext_hex"],
        },
    ).json()

    assert decrypted["sucesso"] is True
    assert decrypted["plaintext"] == "mensagem de verdade"


def test_decrypt_with_wrong_key_fails_gracefully(client):
    encrypted = client.post("/security-demo/encrypt", json={"plaintext": "abc"}).json()
    wrong_key = "00" * 32

    response = client.post(
        "/security-demo/decrypt",
        json={
            "key_hex": wrong_key,
            "nonce_hex": encrypted["nonce_hex"],
            "ciphertext_hex": encrypted["ciphertext_hex"],
        },
    )

    assert response.status_code == 200  # nunca 500 — falha é um resultado normal, não uma exceção
    assert response.json()["sucesso"] is False


def test_decrypt_with_malformed_hex_does_not_crash(client):
    response = client.post(
        "/security-demo/decrypt",
        json={"key_hex": "isso-nao-e-hex", "nonce_hex": "tambem-nao", "ciphertext_hex": "nem-isso"},
    )

    assert response.status_code == 200
    assert response.json()["sucesso"] is False


def test_tamper_demo_shows_original_succeeds_and_tampered_fails(client):
    response = client.post("/security-demo/tamper-demo", json={"plaintext": "dado importante"})

    assert response.status_code == 200
    body = response.json()
    assert body["decriptografia_do_original"]["sucesso"] is True
    assert body["decriptografia_do_original"]["plaintext"] == "dado importante"
    assert body["decriptografia_do_adulterado"]["sucesso"] is False


def test_quiz_returns_questions(client):
    response = client.get("/security-demo/quiz")

    assert response.status_code == 200
    body = response.json()
    assert len(body["perguntas"]) >= 3
    for question in body["perguntas"]:
        assert 0 <= question["resposta_correta_index"] < len(question["opcoes"])
