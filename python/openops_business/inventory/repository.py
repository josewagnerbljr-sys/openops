"""
openops_business.inventory.repository
======================================

Persistência de movimentos de estoque. A tabela referencia `products`
via chave estrangeira — o SQLite não exige que a tabela referenciada já
exista no momento da criação (só valida a integridade em tempo de
INSERT, com `PRAGMA foreign_keys = ON`, já configurado em
`openops_core.db.Database`), então não há acoplamento de ordem entre as
migrations dos dois módulos.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from openops_core.db import Database, Migration
from openops_core.errors import NotFoundError

from .models import StockMovement

INVENTORY_MIGRATIONS = [
    Migration(
        version=1,
        name="create_stock_movements_table",
        namespace="inventory",
        sql="""
        CREATE TABLE stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            reason TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id)
        );
        CREATE INDEX idx_stock_movements_product ON stock_movements (product_id);
        """,
    ),
]


def _row_to_movement(row: sqlite3.Row) -> StockMovement:
    return StockMovement(
        id=row["id"],
        product_id=row["product_id"],
        movement_type=row["movement_type"],
        quantity=row["quantity"],
        reason=row["reason"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


class StockMovementRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def create(self, movement: StockMovement) -> StockMovement:
        now = datetime.now(timezone.utc).isoformat()
        cursor = self._db.execute(
            """
            INSERT INTO stock_movements (product_id, movement_type, quantity, reason, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (movement.product_id, movement.movement_type, movement.quantity, movement.reason, now),
        )
        return self.get(cursor.lastrowid)

    def get(self, movement_id: int) -> StockMovement:
        rows = self._db.query("SELECT * FROM stock_movements WHERE id = ?", (movement_id,))
        if not rows:
            raise NotFoundError(
                f"movimento {movement_id} não encontrado", details={"id": movement_id}
            )
        return _row_to_movement(rows[0])

    def list(self, *, product_id: int | None = None) -> list[StockMovement]:
        if product_id is not None:
            rows = self._db.query(
                "SELECT * FROM stock_movements WHERE product_id = ? ORDER BY created_at DESC",
                (product_id,),
            )
        else:
            rows = self._db.query("SELECT * FROM stock_movements ORDER BY created_at DESC")
        return [_row_to_movement(row) for row in rows]
