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
from datetime import date, datetime, timezone

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
    Migration(
        version=2,
        name="add_batch_and_expiry_to_stock_movements",
        namespace="inventory",
        sql="""
        ALTER TABLE stock_movements ADD COLUMN batch_number TEXT NOT NULL DEFAULT '';
        ALTER TABLE stock_movements ADD COLUMN expiry_date TEXT;
        CREATE INDEX idx_stock_movements_expiry ON stock_movements (expiry_date)
            WHERE expiry_date IS NOT NULL;
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
        batch_number=row["batch_number"],
        expiry_date=date.fromisoformat(row["expiry_date"]) if row["expiry_date"] else None,
        created_at=datetime.fromisoformat(row["created_at"]),
    )


class StockMovementRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def create(self, movement: StockMovement) -> StockMovement:
        now = datetime.now(timezone.utc).isoformat()
        cursor = self._db.execute(
            """
            INSERT INTO stock_movements
                (product_id, movement_type, quantity, reason, batch_number, expiry_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                movement.product_id,
                movement.movement_type,
                movement.quantity,
                movement.reason,
                movement.batch_number,
                movement.expiry_date.isoformat() if movement.expiry_date else None,
                now,
            ),
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

    def list_expiring_batches(self, *, on_or_before: date) -> list[StockMovement]:
        """Lotes recebidos (movimentos "in" com validade preenchida) cuja
        validade cai em ``on_or_before`` ou antes — ordenados por validade
        ascendente (FEFO: *first-expire-first-out*), o critério correto de
        rodízio para uma farmácia.

        Nota de escopo: esta consulta informa lotes recebidos que estão
        vencendo, mas ainda não deduz automaticamente o quanto desse lote
        já foi baixado por saídas — rastreamento de saldo remanescente por
        lote é a próxima fatia natural deste módulo, não implementada aqui.
        """
        rows = self._db.query(
            """
            SELECT * FROM stock_movements
            WHERE movement_type = 'in'
              AND expiry_date IS NOT NULL
              AND expiry_date <= ?
            ORDER BY expiry_date ASC
            """,
            (on_or_before.isoformat(),),
        )
        return [_row_to_movement(row) for row in rows]
