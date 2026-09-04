"""
openops_api.sbom
=================

Expõe o SBOM (Software Bill of Materials) do ambiente Python via HTTP —
o mesmo artefato gerado em `release.yml` (formato CycloneDX), só que
consultável em tempo real, sem precisar baixar o release. O arquivo é
gerado durante o *build* da imagem Docker (ver `python/Dockerfile`),
nunca em tempo de execução — a imagem final não tem `cyclonedx-bom`
instalado, só o JSON estático já pronto.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import APIRouter, Response

router = APIRouter(prefix="/sbom", tags=["sbom"])


def _sbom_path() -> Path:
    return Path(os.environ.get("OPENOPS_SBOM_PATH", "sbom.json"))


@router.get("")
def get_sbom() -> Response:
    """Devolve o SBOM em CycloneDX JSON, se ele existir. Rodando fora do
    Docker (`uvicorn` direto), esse arquivo normalmente não existe —
    devolve uma mensagem explicando isso, em vez de dar erro 500.
    """
    path = _sbom_path()
    if not path.exists():
        return Response(
            content=json.dumps(
                {
                    "disponivel": False,
                    "motivo": (
                        "SBOM não encontrado neste ambiente. Ele é gerado durante o "
                        "build da imagem Docker — rode via `docker compose up` para "
                        "ver o SBOM real, ou baixe o SBOM de qualquer release em "
                        "github.com/josewagnerbljr-sys/openops/releases."
                    ),
                }
            ),
            media_type="application/json",
            status_code=200,
        )

    return Response(content=path.read_text(encoding="utf-8"), media_type="application/json")
