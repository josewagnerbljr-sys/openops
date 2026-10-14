# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""
openops_web.users
==================

Usuários do micro-site (tabela ``web_users``). Segue o mesmo padrão dos
módulos de negócio: migration versionada, regras no domínio, SQL isolado
aqui, e nenhuma dependência de HTTP.

Regras de negócio que importam (e têm teste):

- o **primeiro** usuário é criado pela tela de configuração inicial (ou
  pelo comando ``openops.py init``) e é sempre ``admin``;
- o sistema **nunca fica sem administrador**: não dá para rebaixar nem
  apagar o último admin (senão ninguém conseguiria gerenciar usuários);
- a mensagem de login errado é a mesma para "usuário não existe" e
  "senha errada".
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from openops_core.db import Database, Migration
from openops_core.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from openops_core.roles import ROLE_LEVELS

from .security import UnauthenticatedError, burn_password_time, hash_password, validate_password_strength, verify_password

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")

WEB_USER_MIGRATIONS = [
    Migration(
        version=1,
        name="create_web_users_table",
        namespace="web",
        sql="""
        CREATE TABLE web_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_login_at TEXT
        );
        """,
    ),
]


@dataclass(frozen=True)
class WebUser:
    id: int
    username: str
    role: str
    created_at: str
    last_login_at: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at,
            "last_login_at": self.last_login_at,
        }


def _row_to_user(row: sqlite3.Row) -> WebUser:
    return WebUser(
        id=row["id"],
        username=row["username"],
        role=row["role"],
        created_at=row["created_at"],
        last_login_at=row["last_login_at"],
    )


def validate_username(username: object) -> str:
    if not isinstance(username, str) or not USERNAME_PATTERN.match(username):
        raise ValidationError(
            "usuário inválido",
            details={"username": "use de 3 a 32 caracteres: letras, números, ponto, hífen ou _"},
        )
    return username


def validate_role(role: object) -> str:
    if role not in ROLE_LEVELS:
        raise ValidationError("papel inválido", details={"role": f"use um de {sorted(ROLE_LEVELS)}"})
    return str(role)


class UserStore:
    def __init__(self, db: Database) -> None:
        self._db = db
        self._db.migrate(WEB_USER_MIGRATIONS)

    # -- consultas ---------------------------------------------------------

    def count(self) -> int:
        return self._db.query("SELECT COUNT(*) AS n FROM web_users")[0]["n"]

    def count_admins(self) -> int:
        return self._db.query("SELECT COUNT(*) AS n FROM web_users WHERE role = 'admin'")[0]["n"]

    def list(self) -> list[WebUser]:
        rows = self._db.query("SELECT * FROM web_users ORDER BY username COLLATE NOCASE")
        return [_row_to_user(r) for r in rows]

    def get(self, user_id: int) -> WebUser:
        rows = self._db.query("SELECT * FROM web_users WHERE id = ?", (user_id,))
        if not rows:
            raise NotFoundError(f"usuário {user_id} não encontrado", details={"id": user_id})
        return _row_to_user(rows[0])

    def get_by_username(self, username: str) -> WebUser | None:
        rows = self._db.query("SELECT * FROM web_users WHERE username = ?", (username,))
        return _row_to_user(rows[0]) if rows else None

    # -- escrita -----------------------------------------------------------

    def create(self, *, username: str, password: str, role: str = "viewer") -> WebUser:
        validate_username(username)
        validate_role(role)
        validate_password_strength(password)
        try:
            cursor = self._db.execute(
                "INSERT INTO web_users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (username, hash_password(password), role, datetime.now(timezone.utc).isoformat()),
            )
        except sqlite3.IntegrityError as exc:
            raise ConflictError(f"o usuário '{username}' já existe", details={"username": username}) from exc
        return self.get(cursor.lastrowid)

    def create_first_admin(self, *, username: str, password: str) -> WebUser:
        """Cria o admin inicial. Só funciona enquanto não existe nenhum usuário."""
        if self.count() > 0:
            raise ConflictError("a configuração inicial já foi concluída")
        return self.create(username=username, password=password, role="admin")

    def set_role(self, user_id: int, role: str) -> WebUser:
        validate_role(role)
        current = self.get(user_id)
        if current.role == "admin" and role != "admin" and self.count_admins() <= 1:
            raise ConflictError("não é possível rebaixar o último administrador")
        self._db.execute("UPDATE web_users SET role = ? WHERE id = ?", (role, user_id))
        return self.get(user_id)

    def delete(self, user_id: int) -> None:
        current = self.get(user_id)
        if current.role == "admin" and self.count_admins() <= 1:
            raise ConflictError("não é possível apagar o último administrador")
        self._db.execute("DELETE FROM web_users WHERE id = ?", (user_id,))

    def change_password(self, user_id: int, *, current_password: str, new_password: str) -> None:
        validate_password_strength(new_password)
        rows = self._db.query("SELECT password_hash FROM web_users WHERE id = ?", (user_id,))
        if not rows:
            raise NotFoundError(f"usuário {user_id} não encontrado")
        if not verify_password(current_password, rows[0]["password_hash"]):
            raise AuthorizationError("senha atual incorreta")
        self._db.execute(
            "UPDATE web_users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user_id)
        )

    def reset_password(self, username: str, new_password: str) -> None:
        """Redefine a senha sem exigir a atual — só deve ser chamado por quem tem
        acesso ao computador (comando ``openops.py reset-password``), que é a
        saída para "esqueci a senha do administrador".
        """
        validate_password_strength(new_password)
        user = self.get_by_username(username)
        if user is None:
            raise NotFoundError(f"usuário '{username}' não encontrado", details={"username": username})
        self._db.execute(
            "UPDATE web_users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user.id)
        )

    # -- login -------------------------------------------------------------

    def authenticate(self, *, username: str, password: str) -> WebUser:
        """Confere usuário e senha. A mesma exceção/mensagem para "não
        existe" e "senha errada", gastando o mesmo tempo nos dois casos.
        """
        invalid = UnauthenticatedError("usuário ou senha incorretos")
        if not isinstance(username, str) or not isinstance(password, str) or len(password) > 256:
            raise invalid

        rows = self._db.query("SELECT * FROM web_users WHERE username = ?", (username,))
        if not rows:
            burn_password_time(password)
            raise invalid
        if not verify_password(password, rows[0]["password_hash"]):
            raise invalid

        self._db.execute(
            "UPDATE web_users SET last_login_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), rows[0]["id"]),
        )
        return self.get(rows[0]["id"])
