"""
openops_business.customers.models
==================================

Modelo de domínio de Cliente — segundo módulo do Business OS (Fase 2 do
roadmap). Segue exatamente o mesmo padrão de `products.models`: domínio
imutável, validação no `__post_init__`, atualização via `with_updates`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from openops_core.errors import ValidationError


def _is_valid_email(email: str) -> bool:
    """Validação intencionalmente simples (não é RFC 5322 completo): só
    o suficiente para pegar erros de digitação óbvios, sem rejeitar
    e-mails legítimos por serem "incomuns". Validação de e-mail de
    verdade é confirmar entrega, não regex.
    """
    if email.count("@") != 1:
        return False
    local, _, domain = email.partition("@")
    return bool(local) and "." in domain and not domain.startswith(".") and not domain.endswith(".")


@dataclass(frozen=True)
class Customer:
    """Um cliente cadastrado.

    Attributes:
        id: identificador numérico, atribuído pelo repositório.
        name: nome do cliente — não pode ser vazio.
        email: opcional; se informado, precisa ter formato válido.
        phone: opcional, sem validação de formato (varia por país/uso).
        document: opcional (CPF/CNPJ ou equivalente) — armazenado como
            veio, sem validação de dígito verificador nesta fase.
        created_at / updated_at: timestamps UTC, geridos pelo repositório.
    """

    name: str
    email: str | None = None
    phone: str | None = None
    document: str | None = None
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        errors: dict[str, str] = {}

        if not self.name or not self.name.strip():
            errors["name"] = "não pode ser vazio"

        if self.email is not None and not _is_valid_email(self.email):
            errors["email"] = "formato inválido"

        if errors:
            raise ValidationError("dados de cliente inválidos", details=errors)

    def with_updates(self, **changes: object) -> "Customer":
        """Devolve uma nova instância com os campos indicados alterados,
        preservando id/created_at (mesmo padrão de `Product.with_updates`).
        """
        data = {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "document": self.document,
            "id": self.id,
            "created_at": self.created_at,
        }
        data.update(changes)
        data["updated_at"] = datetime.now(timezone.utc)
        return Customer(**data)
