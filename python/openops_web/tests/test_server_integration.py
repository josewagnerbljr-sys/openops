# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""Teste de integração com um servidor HTTP REAL em porta livre."""

import http.client
import json
import threading

import pytest

from openops_web import WebApp, make_server


@pytest.fixture
def server():
    app = WebApp(db_path=":memory:", secret=b"s" * 32)
    httpd = make_server(app, "127.0.0.1", 0)  # porta 0 = o sistema operacional escolhe uma livre
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd.server_address[1]
    httpd.shutdown()
    httpd.server_close()
    app.close()


def request(port, method, path, body=None, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    payload = json.dumps(body) if body is not None else None
    conn.request(method, path, body=payload, headers=headers or {})
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return response, data


def test_full_flow_over_real_socket(server):
    page, html = request(server, "GET", "/")
    assert page.status == 200 and b"OpenOps" in html
    assert page.getheader("Content-Security-Policy")

    setup, data = request(server, "POST", "/api/setup", {"username": "admin", "password": "senha-forte-123"})
    token = json.loads(data)["token"]
    assert setup.status == 201

    auth = {"Authorization": f"Bearer {token}"}
    created, data = request(server, "POST", "/api/products", {"name": "Caneca", "price": 10, "stock": 5}, auth)
    assert created.status == 201

    listed, data = request(server, "GET", "/api/products", headers=auth)
    assert [p["name"] for p in json.loads(data)["products"]] == ["Caneca"]


def test_dns_rebinding_host_is_rejected_on_loopback(server):
    response, _ = request(server, "GET", "/api/health", headers={"Host": "evil.example.com"})

    assert response.status == 421


def test_huge_content_length_is_refused_before_reading(server):
    response, _ = request(server, "POST", "/api/login", headers={"Content-Length": "99999999"})

    assert response.status == 413


def test_server_header_does_not_reveal_python_version(server):
    response, _ = request(server, "GET", "/api/health")

    assert "Python" not in (response.getheader("Server") or "")
