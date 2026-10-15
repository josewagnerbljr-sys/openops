# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""
openops_web.security
=====================

Primitivas de segurança do micro-site, escritas **só com a biblioteca
padrão do Python** (``hashlib.scrypt``, ``hmac``, ``secrets``).

Por que não reaproveitar Argon2 + PyJWT de ``openops_core.auth``?
Porque o objetivo do micro-site é rodar com ``python openops.py serve``
em qualquer máquina, sem ``pip install`` e sem conhecimento técnico.
``scrypt`` é um KDF *memory-hard* aprovado pela OWASP (a segunda opção,
depois do Argon2id) e já vem no Python; tokens assinados com HMAC-SHA256
cobrem o mesmo papel do JWT para uma aplicação de processo único.

Nada aqui conhece HTTP, banco de dados ou a interface — são funções e
classes pequenas e testáveis isoladamente.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from pathlib import Path
from typing import Callable

from openops_core.errors import AuthorizationError, ValidationError

# --------------------------------------------------------------------------
# Senhas (scrypt)
# --------------------------------------------------------------------------

#: Parâmetros do scrypt. N=2**14, r=8, p=1 usa ~16 MiB de RAM por hash —
#: o mínimo recomendado pela OWASP para scrypt interativo.
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 32

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 256  # evita DoS por senhas gigantes


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def validate_password_strength(password: str) -> None:
    """Regras mínimas de senha. Levanta ``ValidationError`` com a razão."""
    if not isinstance(password, str):
        raise ValidationError("senha inválida", details={"password": "deve ser texto"})
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"a senha precisa ter pelo menos {MIN_PASSWORD_LENGTH} caracteres",
            details={"password": f"mínimo de {MIN_PASSWORD_LENGTH} caracteres"},
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValidationError(
            "senha longa demais", details={"password": f"máximo de {MAX_PASSWORD_LENGTH} caracteres"}
        )
    if password.strip() == "" or len(set(password)) < 3:
        raise ValidationError(
            "escolha uma senha menos previsível", details={"password": "muito simples"}
        )


def hash_password(password: str) -> str:
    """Devolve ``scrypt$N$r$p$salt$hash`` — o formato carrega os próprios
    parâmetros, então dá para aumentar o custo no futuro sem invalidar
    hashes antigos.
    """
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_SCRYPT_DKLEN
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${_b64e(salt)}${_b64e(digest)}"


def verify_password(password: str, stored: str) -> bool:
    """Compara em tempo constante. Hash malformado → ``False`` (nunca exceção)."""
    try:
        scheme, n, r, p, salt_b64, hash_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        expected = _b64d(hash_b64)
        candidate = hashlib.scrypt(
            password.encode("utf-8"),
            salt=_b64d(salt_b64),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, expected)


#: Hash descartável usado para gastar o mesmo tempo quando o usuário não
#: existe — sem isso, o tempo de resposta revelaria quais usernames são
#: válidos (enumeração de usuários por timing).
_DUMMY_HASH = hash_password("openops-dummy-password")


def burn_password_time(password: str) -> None:
    verify_password(password, _DUMMY_HASH)


# --------------------------------------------------------------------------
# Tokens de sessão assinados (HMAC-SHA256)
# --------------------------------------------------------------------------


class UnauthenticatedError(AuthorizationError):
    """Sem sessão válida (HTTP 401) — diferente de ``AuthorizationError``
    puro, que significa "logado, mas sem permissão" (HTTP 403).
    """

    code = "unauthenticated"


class TokenSigner:
    """Emite e valida tokens ``<payload>.<assinatura>``.

    O token só carrega ``sub`` (usuário) e ``exp``. O **papel não vai no
    token**: é lido do banco a cada requisição, então rebaixar ou apagar
    um usuário vale imediatamente, em vez de só quando o token expirar.
    """

    def __init__(self, secret: bytes, *, clock: Callable[[], float] = time.time) -> None:
        if len(secret) < 32:
            raise ValidationError("a chave de assinatura precisa ter pelo menos 32 bytes")
        self._secret = secret
        self._clock = clock

    def _sign(self, payload_b64: str) -> str:
        mac = hmac.new(self._secret, payload_b64.encode("ascii"), hashlib.sha256).digest()
        return _b64e(mac)

    def issue(self, username: str, *, ttl_seconds: int) -> str:
        payload = {"sub": username, "exp": int(self._clock()) + ttl_seconds}
        payload_b64 = _b64e(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        return f"{payload_b64}.{self._sign(payload_b64)}"

    def verify(self, token: str) -> str:
        """Devolve o ``username`` do token ou levanta ``UnauthenticatedError``."""
        try:
            payload_b64, signature = token.split(".")
        except (ValueError, AttributeError):
            raise UnauthenticatedError("sessão inválida, entre novamente") from None

        if not hmac.compare_digest(signature, self._sign(payload_b64)):
            raise UnauthenticatedError("sessão inválida, entre novamente")

        try:
            payload = json.loads(_b64d(payload_b64))
            username, expires_at = payload["sub"], int(payload["exp"])
        except (ValueError, KeyError, TypeError):
            raise UnauthenticatedError("sessão inválida, entre novamente") from None

        if self._clock() >= expires_at:
            raise UnauthenticatedError("sessão expirada, entre novamente")
        return str(username)


def load_or_create_secret(path: str | os.PathLike[str] | None) -> bytes:
    """Chave de assinatura persistente, para que reiniciar o servidor não
    deslogue todo mundo. Fica em um arquivo ao lado do banco, criado com
    permissão ``0600`` (só o dono lê). Sem caminho (banco em memória) →
    chave aleatória só desta execução.
    """
    env_value = os.environ.get("OPENOPS_SECRET")
    if env_value:
        return hashlib.sha256(env_value.encode("utf-8")).digest()
    if path is None:
        return secrets.token_bytes(32)

    secret_path = Path(path)
    if secret_path.exists():
        data = secret_path.read_bytes()
        if len(data) >= 32:
            return data

    secret = secrets.token_bytes(32)
    # os.open com 0o600 evita a janela em que o arquivo existiria legível
    # por outros usuários antes de um chmod posterior.
    fd = os.open(secret_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(secret)
    return secret


# --------------------------------------------------------------------------
# Proteção contra força bruta
# --------------------------------------------------------------------------


class LoginThrottle:
    """Bloqueia temporariamente um par (usuário, IP) após falhas seguidas.

    Em memória, de propósito: para uma instalação de processo único é
    suficiente, e reiniciar o servidor não deve ser um "reset" gratuito
    do bloqueio de um atacante *só* se o processo reiniciar — o custo
    real de scrypt por tentativa já limita a velocidade do ataque.
    """

    def __init__(
        self,
        *,
        max_failures: int = 5,
        window_seconds: int = 300,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max = max_failures
        self._window = window_seconds
        self._clock = clock
        self._failures: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> list[float]:
        recent = [t for t in self._failures.get(key, []) if now - t < self._window]
        if recent:
            self._failures[key] = recent
        else:
            self._failures.pop(key, None)
        return recent

    def retry_after(self, key: str) -> int:
        """Segundos até poder tentar de novo (0 = liberado)."""
        with self._lock:
            now = self._clock()
            recent = self._prune(key, now)
            if len(recent) < self._max:
                return 0
            return max(1, int(self._window - (now - recent[0])) + 1)

    def record_failure(self, key: str) -> None:
        with self._lock:
            now = self._clock()
            self._prune(key, now)
            self._failures.setdefault(key, []).append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)
