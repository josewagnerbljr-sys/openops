"""
openops_business.inventory.models
==================================

Modelo de domínio de movimentação de estoque — terceiro módulo do
Business OS (Fase 2 do roadmap). Diferente de Produtos e Clientes, este
módulo não é um cadastro isolado: ele **depende** do módulo de Produtos
(cada movimento se refere a um produto existente) e é o primeiro lugar
do projeto onde módulos de negócio conversam entre si — exatamente o
tipo de acoplamento que o `EventBus` da Fase 1 existe para mediar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from openops_core.errors import ValidationError

MOVEMENT_TYPES = frozenset({"in", "out", "adjustment"})


@dataclass(frozen=True)
class StockMovement:
    """Um movimento de estoque já registrado (imutável, histórico).

    Attributes:
        product_id: produto afetado.
        movement_type: "in" (entrada), "out" (saída) ou "adjustment"
            (ajuste — define o estoque para um valor absoluto, usado em
            correções de inventário físico).
        quantity: para "in"/"out", a quantidade movimentada (sempre
            positiva). Para "adjustment", o novo nível absoluto de
            estoque (pode ser zero).
        reason: motivo opcional, para auditoria (ex.: "recebimento NF
            1234", "perda por validade", "contagem de inventário").
        id / created_at: atribuídos pelo repositório.
    """

    product_id: int
    movement_type: str
    quantity: int
    reason: str = ""
    id: int | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        errors: dict[str, str] = {}

        if self.movement_type not in MOVEMENT_TYPES:
            errors["movement_type"] = f"deve ser um de {sorted(MOVEMENT_TYPES)}"
        if self.quantity < 0:
            errors["quantity"] = "não pode ser negativa"

        if errors:
            raise ValidationError("movimento de estoque inválido", details=errors)


def apply_movement(current_stock: int, movement_type: str, quantity: int) -> int:
    """Calcula o novo nível de estoque resultante de um movimento, sem
    tocar em banco — função pura, testável isoladamente (inclusive por
    propriedade) e reutilizável tanto pelo serviço quanto por quem
    quiser simular "e se" sem persistir nada.

    Levanta ValidationError se uma saída ("out") deixaria o estoque
    negativo — estoque negativo nunca é um estado válido no OpenOps.
    """
    if movement_type == "in":
        return current_stock + quantity
    if movement_type == "out":
        if quantity > current_stock:
            raise ValidationError(
                "estoque insuficiente para esta saída",
                details={"estoque_atual": current_stock, "quantidade_solicitada": quantity},
            )
        return current_stock - quantity
    if movement_type == "adjustment":
        return quantity
    raise ValidationError(f"tipo de movimento desconhecido: {movement_type!r}")
