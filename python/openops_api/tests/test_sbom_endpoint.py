import json

import pytest
from fastapi.testclient import TestClient

from openops_core.registry import ModuleRegistry
from openops_api.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app(db_path=":memory:", registry=ModuleRegistry(), jwt_secret="x" * 32)
    return TestClient(app)


def test_sbom_endpoint_when_file_missing(client, monkeypatch, tmp_path):
    monkeypatch.setenv("OPENOPS_SBOM_PATH", str(tmp_path / "nao-existe.json"))

    response = client.get("/sbom")

    assert response.status_code == 200
    body = response.json()
    assert body["disponivel"] is False


def test_sbom_endpoint_when_file_exists(client, monkeypatch, tmp_path):
    sbom_file = tmp_path / "sbom.json"
    sbom_file.write_text(json.dumps({"bomFormat": "CycloneDX", "specVersion": "1.6", "components": []}))
    monkeypatch.setenv("OPENOPS_SBOM_PATH", str(sbom_file))

    response = client.get("/sbom")

    assert response.status_code == 200
    body = response.json()
    assert body["bomFormat"] == "CycloneDX"
