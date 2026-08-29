"""
openops_core.db
================

Camada de banco base: conexão SQLite e um executor de migrations
versionadas — a implementação concreta do princípio "Migrações de banco
versionadas" descrito no item 10 do ARCHITECTURE.md. SQLite é o padrão
para desenvolvimento e para instalações pequenas (fork-friendly: zero
configuração de servidor externo); um backend PostgreSQL poderá ser
adicionado depois atrás da mesma interface, sem mudar os módulos de
negócio que dependerem dela.
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterator

from .errors import MaintenanceError, ValidationError


@dataclass(frozen=True)
class Migration:
    """Uma migration versionada.

    Attributes:
        version: inteiro positivo, único, aplicado em ordem crescente.
        name: identificador legível (ex.: "create_products_table").
        sql: um ou mais statements SQL (``executescript``-compatível).
    """

    version: int
    name: str
    sql: str

    def __post_init__(self) -> None:
        if self.version <= 0:
            raise ValidationError("version da migration deve ser um inteiro positivo")
        if not self.name.strip():
            raise ValidationError("name da migration não pode ser vazio")


_MIGRATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS _migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL
)
"""


class Database:
    """Wrapper fino sobre uma conexão SQLite, com migrations versionadas.

    Não é um ORM — deliberadamente. Módulos de negócio das fases
    seguintes decidem seu próprio nível de abstração em cima disto;
    esta camada garante apenas conexão, integridade referencial
    (``PRAGMA foreign_keys``) e histórico de migrations confiável.
    """

    def __init__(self, path: str = ":memory:") -> None:
        self.path = path
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.RLock()

    def connect(self) -> sqlite3.Connection:
        with self._lock:
            if self._conn is None:
                self._conn = sqlite3.connect(self.path, check_same_thread=False)
                self._conn.execute("PRAGMA foreign_keys = ON")
                self._conn.execute(_MIGRATIONS_TABLE_SQL)
                self._conn.commit()
            return self._conn

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def __enter__(self) -> "Database":
        self.connect()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def applied_versions(self) -> set[int]:
        conn = self.connect()
        rows = conn.execute("SELECT version FROM _migrations").fetchall()
        return {row[0] for row in rows}

    def migrate(self, migrations: list[Migration]) -> list[int]:
        """Aplica, em ordem de versão, as migrations ainda não aplicadas.

        Cada migration roda em sua própria transação: uma falha não
        deixa o banco num estado parcialmente migrado silenciosamente —
        levanta :class:`MaintenanceError` com a versão e o motivo exatos.
        """

        versions = [m.version for m in migrations]
        if len(versions) != len(set(versions)):
            raise MaintenanceError("existem migrations com o mesmo número de version")

        conn = self.connect()
        already_applied = self.applied_versions()
        newly_applied: list[int] = []

        for migration in sorted(migrations, key=lambda m: m.version):
            if migration.version in already_applied:
                continue
            try:
                conn.executescript(migration.sql)
                conn.execute(
                    "INSERT INTO _migrations (version, name, applied_at) VALUES (?, ?, ?)",
                    (migration.version, migration.name, datetime.now(timezone.utc).isoformat()),
                )
                conn.commit()
                newly_applied.append(migration.version)
            except sqlite3.Error as exc:
                conn.rollback()
                raise MaintenanceError(
                    f"falha ao aplicar migration {migration.version} ('{migration.name}'): {exc}",
                    details={"version": migration.version, "name": migration.name},
                ) from exc

        return newly_applied

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        """Executa um statement (INSERT/UPDATE/DELETE) e comita."""
        conn = self.connect()
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor

    def query(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        """Executa um SELECT e devolve as linhas, com acesso por nome de coluna."""
        conn = self.connect()
        conn.row_factory = sqlite3.Row
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.row_factory = None


@contextmanager
def database(path: str = ":memory:") -> Iterator[Database]:
    """Context manager de conveniência: ``with database(path) as db: ...``."""
    db = Database(path)
    try:
        db.connect()
        yield db
    finally:
        db.close()
