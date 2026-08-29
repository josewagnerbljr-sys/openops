"""
openops_business.products.repository
=====================================

Persistência de produtos, sobre a camada de banco base
(``openops_core.db``). Todo acesso a SQL fica isolado aqui — o resto do
módulo (serviço, API) nunca monta uma query diretamente, o que permite
trocar SQLite por outro backend no futuro sem tocar em regra de negócio.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from openops_core.db import Database, Migration
from openops_core.errors import ConflictError, NotFoundError

from .models import Product

PRODUCTS_MIGRATIONS = [
    Migration(
        version=1,
        name="create_products_table",
        sql="""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            category TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX idx_products_category ON products (category);
        """,
    ),
]


def _row_to_product(row: sqlite3.Row) -> Product:
    return Product(
        id=row["id"],
        name=row["name"],
        price=row["price"],
        stock=row["stock"],
        category=row["category"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


class ProductRepository:
    """Repositório de produtos. Requer que ``PRODUCTS_MIGRATIONS`` já
    tenha sido aplicado ao banco (o serviço faz isso na inicialização).
    """

    def __init__(self, db: Database) -> None:
        self._db = db

    def create(self, product: Product) -> Product:
        now = datetime.now(timezone.utc).isoformat()
        try:
            cursor = self._db.execute(
                """
                INSERT INTO products (name, price, stock, category, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (product.name, product.price, product.stock, product.category, now, now),
            )
        except sqlite3.IntegrityError as exc:
            raise ConflictError(
                f"já existe um produto chamado '{product.name}'",
                details={"name": product.name},
            ) from exc

        return self.get(cursor.lastrowid)

    def get(self, product_id: int) -> Product:
        rows = self._db.query("SELECT * FROM products WHERE id = ?", (product_id,))
        if not rows:
            raise NotFoundError(f"produto {product_id} não encontrado", details={"id": product_id})
        return _row_to_product(rows[0])

    def list(self, *, category: str | None = None) -> list[Product]:
        if category is not None:
            rows = self._db.query(
                "SELECT * FROM products WHERE category = ? ORDER BY name", (category,)
            )
        else:
            rows = self._db.query("SELECT * FROM products ORDER BY name")
        return [_row_to_product(row) for row in rows]

    def update(self, product_id: int, updated: Product) -> Product:
        # garante que o produto existe antes de tentar atualizar
        self.get(product_id)

        try:
            self._db.execute(
                """
                UPDATE products
                SET name = ?, price = ?, stock = ?, category = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    updated.name,
                    updated.price,
                    updated.stock,
                    updated.category,
                    datetime.now(timezone.utc).isoformat(),
                    product_id,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ConflictError(
                f"já existe um produto chamado '{updated.name}'",
                details={"name": updated.name},
            ) from exc

        return self.get(product_id)

    def delete(self, product_id: int) -> None:
        self.get(product_id)  # levanta NotFoundError se não existir
        self._db.execute("DELETE FROM products WHERE id = ?", (product_id,))
