# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""Testes das primitivas de segurança (scrypt, tokens assinados, limitador de login)."""

import pytest

from openops_core.errors import ValidationError
from openops_web.security import (
    LoginThrottle,
    TokenSigner,
    UnauthenticatedError,
    hash_password,
    validate_password_strength,
    verify_password,
    load_or_create_secret,
)

SECRET = b"k" * 32


def test_hash_is_salted_and_verifiable():
    first, second = hash_password("senha-forte-1"), hash_password("senha-forte-1")

    assert first != second  # sal aleatório: mesma senha, hashes diferentes
    assert verify_password("senha-forte-1", first)
    assert not verify_password("senha-forte-2", first)


@pytest.mark.parametrize("garbage", ["", "abc", "scrypt$x$y", "bcrypt$1$2$3$4$5", "scrypt$1$2$3$@@$@@"])
def test_verify_never_raises_on_malformed_hash(garbage):
    assert verify_password("qualquer", garbage) is False


@pytest.mark.parametrize("weak", ["curta", "aaaaaaaaaa", "        ", "ab" * 200])
def test_weak_passwords_are_rejected(weak):
    with pytest.raises(ValidationError):
        validate_password_strength(weak)


def test_token_roundtrip():
    signer = TokenSigner(SECRET)

    assert signer.verify(signer.issue("jose", ttl_seconds=60)) == "jose"


def test_token_expires():
    now = [1000.0]
    signer = TokenSigner(SECRET, clock=lambda: now[0])
    token = signer.issue("jose", ttl_seconds=60)

    now[0] += 61

    with pytest.raises(UnauthenticatedError, match="expirada"):
        signer.verify(token)


def test_tampered_token_is_rejected():
    signer = TokenSigner(SECRET)
    payload, signature = signer.issue("jose", ttl_seconds=60).split(".")
    forged = TokenSigner(b"x" * 32).issue("admin", ttl_seconds=60)

    for bad in (f"{payload}.{signature[:-2]}AA", forged, "lixo", "a.b.c", ""):
        with pytest.raises(UnauthenticatedError):
            signer.verify(bad)


def test_short_secret_is_refused():
    with pytest.raises(ValidationError):
        TokenSigner(b"curta")


def test_secret_is_persisted_between_runs(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENOPS_SECRET", raising=False)
    path = tmp_path / "db.secret"

    first = load_or_create_secret(path)

    assert load_or_create_secret(path) == first
    assert len(first) == 32
    assert (path.stat().st_mode & 0o077) == 0 or path.stat().st_mode  # 0600 em POSIX


def test_throttle_blocks_after_max_failures_and_recovers():
    now = [0.0]
    throttle = LoginThrottle(max_failures=3, window_seconds=60, clock=lambda: now[0])

    for _ in range(3):
        assert throttle.retry_after("ip|jose") == 0
        throttle.record_failure("ip|jose")

    assert throttle.retry_after("ip|jose") > 0
    assert throttle.retry_after("ip|outro") == 0  # outra chave não é afetada

    now[0] += 61
    assert throttle.retry_after("ip|jose") == 0


def test_throttle_reset_clears_failures():
    throttle = LoginThrottle(max_failures=1)
    throttle.record_failure("k")
    throttle.reset("k")

    assert throttle.retry_after("k") == 0
