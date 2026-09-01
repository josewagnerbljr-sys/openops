"""
openops_core.auth
==================

Autenticação (JWT) e controle de acesso baseado em papel (RBAC) —
Camada 3 ("Access/Runtime") descrita no ARCHITECTURE.md, e o principal
risco documentado como "aceito" no THREAT_MODEL.md até agora. Esta
camada é deliberadamente independente de framework: não importa FastAPI
aqui — a integração com HTTP fica em `openops_api.auth`.

Senhas nunca são armazenadas nem comparadas em texto claro: usamos
Argon2id (via `argon2-cffi`), vencedor da Password Hashing Competition e
recomendado atualmente pela OWASP sobre bcrypt/PBKDF2 para uso geral.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from .db import Database, Migration
from .errors import AuthorizationError, ConflictError, NotFoundError, ValidationError

#: Ordem de privilégio dos papéis — "viewer" só lê, "operator" também
#: cria/edita/apaga, "admin" acumula tudo (hoje equivalente a operator;
#: existe como teto para permissões administrativas futuras, como
#: gerenciar outros usuários).
ROLE_LEVELS: dict[str, int] = {"viewer": 1, "operator": 2, "admin": 3}

AUTH_MIGRATIONS = [
    Migration(
        version=1,
        name="create_users_table",
        namespace="auth",
        sql="""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """,
    ),
]

_hasher = PasswordHasher()


@dataclass(frozen=True)
class User:
    id: int
    username: str
    role: str
    created_at: datetime


@dataclass(frozen=True)
class TokenPayload:
    """O conteúdo verificado de um JWT válido — é o que a API usa para
    saber "quem está chamando e com que papel", sem precisar consultar
    o banco a cada requisição (o token já carrega essa informação,
    assinada e à prova de adulteração).
    """

    username: str
    role: str


class AuthService:
    """Registro, login e verificação de token — o único ponto de
    entrada que o resto do sistema deve usar para autenticação.
    """

    def __init__(self, db: Database, *, secret_key: str, token_ttl_seconds: int = 3600) -> None:
        if not secret_key or len(secret_key) < 16:
            raise ValidationError(
                "secret_key precisa ter pelo menos 16 caracteres — nunca use um valor fraco/padrão em produção"
            )
        self._db = db
        self._db.migrate(AUTH_MIGRATIONS)
        self._secret_key = secret_key
        self._token_ttl_seconds = token_ttl_seconds

    def register(self, *, username: str, password: str, role: str = "viewer") -> User:
        if role not in ROLE_LEVELS:
            raise ValidationError(f"papel inválido: {role!r}", details={"valid_roles": sorted(ROLE_LEVELS)})
        if len(password) < 8:
            raise ValidationError("senha precisa ter pelo menos 8 caracteres")

        # O primeiro usuário cadastrado no sistema vira admin
        # automaticamente — sem isso, ninguém conseguiria promover o
        # primeiro admin (ovo-e-galinha clássico de todo sistema com RBAC).
        is_first_user = self._count_users() == 0
        effective_role = "admin" if is_first_user else role

        password_hash = _hasher.hash(password)
        now = datetime.now(timezone.utc).isoformat()
        try:
            cursor = self._db.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (username, password_hash, effective_role, now),
            )
        except sqlite3.IntegrityError as exc:
            raise ConflictError(f"usuário '{username}' já existe") from exc

        return self._get_by_id(cursor.lastrowid)

    def authenticate(self, *, username: str, password: str) -> str:
        """Verifica usuário/senha e devolve um JWT assinado, válido por
        `token_ttl_seconds`. Levanta AuthorizationError tanto para
        usuário inexistente quanto senha errada — nunca revela qual dos
        dois falhou (evita enumeração de usuários válidos).
        """
        rows = self._db.query("SELECT * FROM users WHERE username = ?", (username,))
        if not rows:
            raise AuthorizationError("usuário ou senha inválidos")

        row = rows[0]
        try:
            _hasher.verify(row["password_hash"], password)
        except VerifyMismatchError:
            raise AuthorizationError("usuário ou senha inválidos") from None

        now = int(time.time())
        payload = {
            "sub": row["username"],
            "role": row["role"],
            "iat": now,
            "exp": now + self._token_ttl_seconds,
        }
        return jwt.encode(payload, self._secret_key, algorithm="HS256")

    def decode_token(self, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthorizationError("token expirado, faça login novamente") from None
        except jwt.InvalidTokenError:
            raise AuthorizationError("token inválido") from None

        return TokenPayload(username=payload["sub"], role=payload["role"])

    def _count_users(self) -> int:
        rows = self._db.query("SELECT COUNT(*) AS n FROM users")
        return rows[0]["n"]

    def _get_by_id(self, user_id: int) -> User:
        rows = self._db.query("SELECT * FROM users WHERE id = ?", (user_id,))
        if not rows:
            raise NotFoundError(f"usuário {user_id} não encontrado")
        row = rows[0]
        return User(
            id=row["id"],
            username=row["username"],
            role=row["role"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )


def role_satisfies(user_role: str, minimum: str) -> bool:
    """Função pura: `user_role` tem privilégio suficiente para `minimum`?
    Separada do resto pra ser trivialmente testável (inclusive por
    propriedade) sem precisar montar um AuthService inteiro.
    """
    return ROLE_LEVELS.get(user_role, 0) >= ROLE_LEVELS.get(minimum, 0)
