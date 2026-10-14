"""
openops_core.config
====================

Carregamento de configuração em camadas (defaults -> arquivo -> variáveis de
ambiente), seguindo o princípio "Security by design / Privacy by design" do
OpenOps: nenhuma configuração sensível tem valor padrão embutido no código,
e variáveis de ambiente sempre têm prioridade sobre arquivos versionados.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    """Erro de carregamento ou validação de configuração."""


@dataclass(frozen=True)
class OpenOpsConfig:
    """Configuração central do OpenOps.

    Attributes:
        environment: "development", "staging" ou "production".
        log_level: nível mínimo de log (DEBUG, INFO, WARNING, ERROR).
        database_url: string de conexão do banco (nunca deve ter default
            fixo em produção; deve vir de variável de ambiente).
        event_bus_backend: "memory" (padrão local) ou outro backend futuro.
        extra: quaisquer chaves adicionais não mapeadas explicitamente,
            preservadas para uso por plugins.
    """

    environment: str = "development"
    log_level: str = "INFO"
    database_url: str | None = None
    event_bus_backend: str = "memory"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_ENV_PREFIX = "OPENOPS_"


def _load_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Arquivo de configuração inválido em {path}: {exc}") from exc


def _load_env(prefix: str = _ENV_PREFIX) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        config_key = key[len(prefix):].lower()
        result[config_key] = value
    return result


def load_config(
    config_path: str | Path | None = None,
    *,
    env_prefix: str = _ENV_PREFIX,
) -> OpenOpsConfig:
    """Monta a configuração final combinando defaults, arquivo e ambiente.

    Ordem de precedência (do menor para o maior): defaults do dataclass ->
    arquivo JSON (se existir) -> variáveis de ambiente prefixadas com
    ``OPENOPS_``.
    """

    merged: dict[str, Any] = {}

    if config_path is not None:
        merged.update(_load_file(Path(config_path)))

    merged.update(_load_env(env_prefix))

    known_fields = {f for f in OpenOpsConfig.__dataclass_fields__}
    known_kwargs = {k: v for k, v in merged.items() if k in known_fields}
    extra_kwargs = {k: v for k, v in merged.items() if k not in known_fields}

    if extra_kwargs:
        known_kwargs["extra"] = extra_kwargs

    return OpenOpsConfig(**known_kwargs)
