"""
openops_business.products.models
=================================

Modelo de domínio de Produto — primeira fatia real do Business OS
(Fase 2 do roadmap, item "Cadastros, produtos"). Validação de regras de
negócio vive aqui, não no repositório nem na API: assim a mesma regra
vale independente de quem chama (API REST, um script de import em lote,
ou um plugin de terceiros).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from openops_core.errors import ValidationError


@dataclass(frozen=True)
class Product:
    """Um produto do catálogo.

    Attributes:
        id: identificador numérico, atribuído pelo repositório na
            criação (``None`` antes de ser persistido).
        name: nome do produto — não pode ser vazio.
        price: preço unitário — deve ser maior que zero.
        stock: quantidade em estoque — não pode ser negativa.
        category: categoria livre (ex.: "bebidas", "insumos").
        created_at / updated_at: timestamps UTC, geridos pelo repositório.
    """

    name: str
    price: float
    stock: int = 0
    category: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        errors: dict[str, str] = {}

        if not self.name or not self.name.strip():
            errors["name"] = "não pode ser vazio"
        if self.price <= 0:
            errors["price"] = "deve ser maior que zero"
        if self.stock < 0:
            errors["stock"] = "não pode ser negativo"

        if errors:
            raise ValidationError("dados de produto inválidos", details=errors)

    def with_updates(self, **changes: object) -> "Product":
        """Devolve uma nova instância com os campos indicados alterados,
        preservando id/created_at e atualizando updated_at para agora.

        Como :class:`Product` é imutável (``frozen=True``), atualizações
        sempre passam por aqui — nunca por mutação direta de atributo.
        """
        data = {
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
            "category": self.category,
            "id": self.id,
            "created_at": self.created_at,
        }
        data.update(changes)
        data["updated_at"] = datetime.now(timezone.utc)
        return Product(**data)
