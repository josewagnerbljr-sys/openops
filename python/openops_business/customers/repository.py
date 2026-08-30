"""
openops_business.customers.repository
======================================

Persistência de clientes via SQLite. O e-mail tem índice único
*parcial* (só quando não-nulo) — permite múltiplos clientes sem e-mail
cadastrado, mas nunca dois clientes com o mesmo e-mail.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from openops_core.db import Database, Migration
from openops_core.errors import ConflictError, NotFoundError

from .models import Customer

CUSTOMERS_MIGRATIONS = [
    Migration(
        version=1,
        name="create_customers_table",
        namespace="customers",
        sql="""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            document TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE UNIQUE INDEX idx_customers_email ON customers (email) WHERE email IS NOT NULL;
        CREATE INDEX idx_customers_name ON customers (name);
        """,
    ),
]


def _row_to_customer(row: sqlite3.Row) -> Customer:
    return Customer(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        phone=row["phone"],
        document=row["document"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


class CustomerRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def create(self, customer: Customer) -> Customer:
        now = datetime.now(timezone.utc).isoformat()
        try:
            cursor = self._db.execute(
                """
                INSERT INTO customers (name, email, phone, document, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (customer.name, customer.email, customer.phone, customer.document, now, now),
            )
        except sqlite3.IntegrityError as exc:
            raise ConflictError(
                f"já existe um cliente com o e-mail '{customer.email}'",
                details={"email": customer.email},
            ) from exc

        return self.get(cursor.lastrowid)

    def get(self, customer_id: int) -> Customer:
        rows = self._db.query("SELECT * FROM customers WHERE id = ?", (customer_id,))
        if not rows:
            raise NotFoundError(f"cliente {customer_id} não encontrado", details={"id": customer_id})
        return _row_to_customer(rows[0])

    def list(self, *, search: str | None = None) -> list[Customer]:
        if search:
            rows = self._db.query(
                "SELECT * FROM customers WHERE name LIKE ? ORDER BY name",
                (f"%{search}%",),
            )
        else:
            rows = self._db.query("SELECT * FROM customers ORDER BY name")
        return [_row_to_customer(row) for row in rows]

    def update(self, customer_id: int, updated: Customer) -> Customer:
        self.get(customer_id)

        try:
            self._db.execute(
                """
                UPDATE customers
                SET name = ?, email = ?, phone = ?, document = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    updated.name,
                    updated.email,
                    updated.phone,
                    updated.document,
                    datetime.now(timezone.utc).isoformat(),
                    customer_id,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ConflictError(
                f"já existe um cliente com o e-mail '{updated.email}'",
                details={"email": updated.email},
            ) from exc

        return self.get(customer_id)

    def delete(self, customer_id: int) -> None:
        self.get(customer_id)
        self._db.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
