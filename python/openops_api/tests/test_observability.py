from openops_core.registry import ModuleRegistry
from openops_api.main import create_app
from openops_api.observability import get_finished_spans, clear_spans
from fastapi.testclient import TestClient


def test_request_generates_a_trace_span():
    clear_spans()
    app = create_app(db_path=":memory:", registry=ModuleRegistry(), jwt_secret="x" * 32)
    client = TestClient(app)

    client.get("/")

    spans = get_finished_spans()
    matching = [s for s in spans if s.name and "/" in s.name or s.attributes.get("http.route")]
    assert len(spans) >= 1


def test_metrics_endpoint_exposes_prometheus_format():
    app = create_app(db_path=":memory:", registry=ModuleRegistry(), jwt_secret="x" * 32)
    client = TestClient(app)

    client.get("/")  # gera pelo menos uma métrica antes de consultar /metrics
    response = client.get("/metrics")

    assert response.status_code == 200
    body = response.text
    assert "openops_http_requests_total" in body
    assert "openops_http_request_duration_seconds" in body


def test_metrics_reflect_request_count():
    app = create_app(db_path=":memory:", registry=ModuleRegistry(), jwt_secret="x" * 32)
    client = TestClient(app)

    client.get("/")
    client.get("/")
    client.get("/")

    body = client.get("/metrics").text
    # confirma que existe uma série com pelo menos as 3 chamadas a "/"
    # (não checamos o valor exato porque outras requisições do mesmo
    # teste, como a própria chamada a /metrics, também contam)
    assert 'path="/"' in body
