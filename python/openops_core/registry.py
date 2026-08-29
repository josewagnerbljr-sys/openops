"""
openops_core.registry
======================

Registry central de módulos do OpenOps. Cada módulo de negócio (Business,
OpenSOP, Operations, Security, etc.) — e cada plugin de terceiros
instalado seguindo o SDK da Fase 11 do roadmap — se registra aqui com
seus metadados. É essa fonte única de verdade que permitirá, nas fases
seguintes, que a API monte suas rotas dinamicamente, que o Structural
Health Engine relate quais módulos estão presentes, e que o CLI liste o
que está instalado sem precisar de import manual em cada lugar.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from .errors import ConflictError, NotFoundError, ValidationError

VALID_CATEGORIES = frozenset(
    {"core", "business", "sop", "operations", "security", "maintenance", "health", "plugin"}
)


@dataclass(frozen=True)
class ModuleInfo:
    """Metadados de um módulo registrado.

    Attributes:
        name: identificador único do módulo (ex.: "inventory", "sop").
        version: versão semântica do módulo (ex.: "0.1.0").
        category: uma das camadas descritas em ARCHITECTURE.md.
        description: resumo de uma linha do que o módulo faz.
        metadata: informação livre adicional (ex.: autor, licença do plugin).
    """

    name: str
    version: str
    category: str = "core"
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValidationError("nome do módulo não pode ser vazio")
        if self.category not in VALID_CATEGORIES:
            raise ValidationError(
                f"categoria '{self.category}' inválida",
                details={"valid_categories": sorted(VALID_CATEGORIES)},
            )


class ModuleRegistry:
    """Registro thread-safe de módulos do OpenOps.

    Um único módulo (por nome) pode estar registrado por vez — registrar
    duas vezes o mesmo nome é um erro explícito (:class:`ConflictError`),
    para pegar cedo o tipo de bug onde um plugin mal escrito sobrescreve
    silenciosamente um módulo do core.
    """

    def __init__(self) -> None:
        self._modules: dict[str, ModuleInfo] = {}
        self._lock = threading.RLock()

    def register(self, info: ModuleInfo) -> None:
        with self._lock:
            if info.name in self._modules:
                raise ConflictError(
                    f"módulo '{info.name}' já está registrado",
                    details={"existing_version": self._modules[info.name].version},
                )
            self._modules[info.name] = info

    def unregister(self, name: str) -> None:
        with self._lock:
            if name not in self._modules:
                raise NotFoundError(f"módulo '{name}' não está registrado")
            del self._modules[name]

    def get(self, name: str) -> ModuleInfo:
        with self._lock:
            try:
                return self._modules[name]
            except KeyError:
                raise NotFoundError(f"módulo '{name}' não está registrado") from None

    def list(self, *, category: str | None = None) -> list[ModuleInfo]:
        with self._lock:
            modules = list(self._modules.values())
        if category is not None:
            modules = [m for m in modules if m.category == category]
        return sorted(modules, key=lambda m: m.name)

    def __contains__(self, name: str) -> bool:
        with self._lock:
            return name in self._modules

    def __len__(self) -> int:
        with self._lock:
            return len(self._modules)

    def clear(self) -> None:
        """Remove todos os módulos registrados. Uso principal: testes."""
        with self._lock:
            self._modules.clear()


#: Registry padrão compartilhado pelo processo. Módulos de negócio devem
#: se registrar aqui a menos que estejam explicitamente testando um
#: registry isolado.
default_registry = ModuleRegistry()


def register_module(
    *,
    name: str,
    version: str,
    category: str = "core",
    description: str = "",
    registry: ModuleRegistry | None = None,
    **metadata: Any,
) -> Callable[[Any], Any]:
    """Decorator de conveniência: registra o módulo e devolve o alvo
    (classe, função ou objeto) inalterado, para uso como::

        @register_module(name="inventory", version="0.1.0", category="business")
        class InventoryModule:
            ...
    """

    target_registry = registry if registry is not None else default_registry

    def decorator(target: Any) -> Any:
        target_registry.register(
            ModuleInfo(
                name=name,
                version=version,
                category=category,
                description=description,
                metadata=metadata,
            )
        )
        return target

    return decorator
