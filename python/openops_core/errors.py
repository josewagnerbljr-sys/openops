"""
openops_core.errors
====================

Hierarquia de exceções do OpenOps. Toda exceção de domínio no projeto
deve herdar de :class:`OpenOpsError`, nunca levantar ``Exception`` crua —
isso permite que a camada de API (Fase 9 do roadmap) mapeie
automaticamente para o código HTTP correto, e que o Structural Health
Engine e o Self-Maintenance Engine categorizem falhas de forma
consistente entre módulos escritos por autores diferentes.
"""

from __future__ import annotations

from typing import Any


class OpenOpsError(Exception):
    """Classe-base de todas as exceções de domínio do OpenOps.

    Attributes:
        code: identificador estável da categoria do erro (ex.:
            "not_found"), pensado para ser consumido por clientes de API
            e por logs estruturados — nunca deve mudar entre versões.
        message: descrição legível por humanos.
        details: contexto adicional livre (ex.: qual campo falhou).
    """

    code: str = "openops_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Serializa o erro para um corpo de resposta de API consistente."""
        return {"error": self.code, "message": self.message, "details": self.details}

    def __repr__(self) -> str:  # pragma: no cover - conveniência de debug
        return f"{type(self).__name__}(message={self.message!r}, details={self.details!r})"


class ValidationError(OpenOpsError):
    """Entrada inválida fornecida pelo usuário ou por um plugin."""

    code = "validation_error"


class NotFoundError(OpenOpsError):
    """Um recurso solicitado não existe."""

    code = "not_found"


class ConflictError(OpenOpsError):
    """A operação conflita com um estado existente (ex.: nome duplicado)."""

    code = "conflict"


class AuthorizationError(OpenOpsError):
    """O ator não tem permissão para executar a operação."""

    code = "authorization_error"


class ConfigurationError(OpenOpsError):
    """Configuração ausente, inválida ou inconsistente."""

    code = "configuration_error"


class IntegrationError(OpenOpsError):
    """Falha ao integrar com um sistema externo (ERP, CRM, plugin de terceiro)."""

    code = "integration_error"


class MaintenanceError(OpenOpsError):
    """Falha em uma operação de manutenção (migration, snapshot, reparo)."""

    code = "maintenance_error"


# Mapeamento de referência para quando a camada de API (Fase 9) for
# implementada — mantido aqui para que a decisão de qual código HTTP
# cada categoria de erro deve gerar fique junto da própria hierarquia,
# não espalhada pelo código dos endpoints.
HTTP_STATUS_BY_ERROR: dict[type[OpenOpsError], int] = {
    ValidationError: 422,
    NotFoundError: 404,
    ConflictError: 409,
    AuthorizationError: 403,
    ConfigurationError: 500,
    IntegrationError: 502,
    MaintenanceError: 500,
    OpenOpsError: 500,
}


def http_status_for(error: OpenOpsError) -> int:
    """Resolve o código HTTP apropriado para uma instância de erro,
    percorrendo a hierarquia de classes (MRO) até achar um mapeamento —
    assim subclasses futuras não precisam ser registradas manualmente
    aqui se já herdarem de uma categoria existente.
    """

    for cls in type(error).__mro__:
        if cls in HTTP_STATUS_BY_ERROR:
            return HTTP_STATUS_BY_ERROR[cls]
    return 500
