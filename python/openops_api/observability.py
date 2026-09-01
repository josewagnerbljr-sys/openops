"""
openops_api.observability
==========================

Instrumentação de observabilidade: rastreamento distribuído
(OpenTelemetry) e métricas no formato Prometheus. É o que separa "a API
funciona" de "dá pra saber por que ela está lenta ou falhando em
produção" — cada requisição HTTP vira um *span* rastreável, e latência
por rota fica exposta em `/metrics`, pronta para um Prometheus real
raspar.

O provedor de tracing é global e configurado uma única vez por processo
(é assim que o OpenTelemetry funciona — instrumentar múltiplas vezes o
mesmo provedor gera avisos, não erros, mas é desnecessário). Em
desenvolvimento/teste usamos um exportador em memória (nada vai pro
console, e os spans ficam inspecionáveis via `get_finished_spans()`);
`configure_console_export()` liga a exportação real para quando o
processo sobe de verdade via `uvicorn`.
"""

from __future__ import annotations

import time

from fastapi import FastAPI, Request, Response
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "openops_http_requests_total",
    "Total de requisições HTTP recebidas",
    ["method", "path", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "openops_http_request_duration_seconds",
    "Duração das requisições HTTP em segundos",
    ["method", "path"],
)

_in_memory_exporter = InMemorySpanExporter()
_provider_configured = False


def _ensure_provider_configured(*, service_name: str = "openops-api") -> None:
    global _provider_configured
    if _provider_configured:
        return

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(SimpleSpanProcessor(_in_memory_exporter))
    trace.set_tracer_provider(provider)
    _provider_configured = True


def configure_console_export() -> None:
    """Liga a exportação de spans para o console — chamado só pela
    instância "de verdade" da API (`uvicorn openops_api.main:app`), não
    pelos testes, para não poluir a saída do pytest com spans.
    """
    _ensure_provider_configured()
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))


def get_finished_spans():
    """Devolve os spans capturados pelo exportador em memória — usado
    pelos testes para provar que uma requisição realmente gerou um
    trace, sem depender de nenhum coletor externo.
    """
    return _in_memory_exporter.get_finished_spans()


def clear_spans() -> None:
    """Limpa os spans capturados — chamado no início de cada teste que
    for inspecionar tracing, para não misturar spans de testes
    anteriores (o exportador em memória é compartilhado pelo processo).
    """
    _in_memory_exporter.clear()


def setup_tracing(app: FastAPI) -> None:
    """Instrumenta automaticamente todas as rotas do app — cada
    requisição HTTP vira um span, com método, rota e status code como
    atributos, sem precisar anotar cada endpoint manualmente.
    """
    _ensure_provider_configured()
    FastAPIInstrumentor.instrument_app(app)


def setup_metrics(app: FastAPI) -> None:
    """Middleware que registra contagem e latência de cada requisição
    (rótulos: método, rota, status code), e expõe `/metrics` no formato
    de texto que o Prometheus espera raspar.
    """

    @app.middleware("http")
    async def record_metrics(request: Request, call_next):
        route_path = request.url.path
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        REQUEST_COUNT.labels(request.method, route_path, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, route_path).observe(duration)

        return response

    @app.get("/metrics", tags=["meta"], include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
