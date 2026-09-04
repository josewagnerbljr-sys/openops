# syntax=docker/dockerfile:1
#
# Build a partir da RAIZ do repositório:
#   docker build -f python/Dockerfile -t openops-api .
#
# Multi-stage: o estágio "builder" instala as dependências numa venv
# isolada; o estágio final copia só a venv pronta + o código-fonte —
# sem cache de pip, sem toolchain de build, sem os arquivos de teste.
# Roda como usuário não-root (item de segurança básico que a maioria
# das imagens Docker publicadas por hobby ignora).

FROM python:3.12-slim AS builder

WORKDIR /build
COPY python/pyproject.toml .
COPY python/openops_core ./openops_core
COPY python/openops_business ./openops_business
COPY python/openops_api ./openops_api

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Gera o SBOM (CycloneDX) real do ambiente durante o build — a
# ferramenta cyclonedx-bom fica só neste estágio "builder", nunca na
# imagem final. Servido depois via GET /sbom.
RUN pip install --no-cache-dir cyclonedx-bom && \
    cyclonedx-py environment --output-format json --output-file /build/sbom.json

FROM python:3.12-slim

RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin openops

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /build/sbom.json ./sbom.json
COPY python/openops_core ./openops_core
COPY python/openops_business ./openops_business
COPY python/openops_api ./openops_api

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    OPENOPS_DB_PATH=/app/data/openops.db \
    OPENOPS_SBOM_PATH=/app/sbom.json

RUN mkdir -p /app/data && chown -R openops:openops /app/data

USER openops
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/', timeout=2)" || exit 1

CMD ["uvicorn", "openops_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
