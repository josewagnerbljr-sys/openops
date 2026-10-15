# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""Testes da aplicação web — sem socket: ``WebApp.handle`` é uma função
de requisição → resposta, então cada teste roda em milissegundos.
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from openops_web import WebApp
from openops_web.security import LoginThrottle

PASSWORD = "senha-forte-123"


@pytest.fixture
def app():
    application = WebApp(db_path=":memory:", secret=b"s" * 32)
    yield application
    application.close()


class Client:
    def __init__(self, app, token=None, ip="127.0.0.1"):
        self.app, self.token, self.ip = app, token, ip

    def call(self, method, path, body=None, headers=None):
        hdrs = dict(headers or {})
        if self.token:
            hdrs["Authorization"] = f"Bearer {self.token}"
        raw = b"" if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
        response = self.app.handle(method, path, hdrs, raw, self.ip)
        is_json = response.headers.get("Content-Type", "").startswith("application/json")
        return response.status, (json.loads(response.body) if is_json else response)

    def get(self, path, **kw): return self.call("GET", path, **kw)
    def post(self, path, body=None, **kw): return self.call("POST", path, body, **kw)
    def put(self, path, body=None, **kw): return self.call("PUT", path, body, **kw)
    def delete(self, path, **kw): return self.call("DELETE", path, **kw)
    def patch(self, path, body=None, **kw): return self.call("PATCH", path, body, **kw)


@pytest.fixture
def admin(app):
    status, data = Client(app).post("/api/setup", {"username": "admin", "password": PASSWORD})
    assert status == 201
    return Client(app, data["token"])


def make_user(app, admin, username, role):
    assert admin.post("/api/users", {"username": username, "password": PASSWORD, "role": role})[0] == 201
    status, data = Client(app).post("/api/login", {"username": username, "password": PASSWORD})
    assert status == 200
    return Client(app, data["token"])


def make_product(client, name="Caneca", price=10.0, stock=10, category="Casa"):
    status, data = client.post("/api/products", {"name": name, "price": price, "stock": stock, "category": category})
    assert status == 201, data
    return data["product"]


# ---------------------------------------------------------------- configuração inicial e login


def test_status_reports_setup_required_then_done(app, admin):
    assert Client(app).get("/api/status")[1]["setup_required"] is False


def test_setup_is_required_on_empty_system(app):
    assert Client(app).get("/api/status")[1]["setup_required"] is True


def test_setup_works_only_once(app, admin):
    status, body = Client(app).post("/api/setup", {"username": "intruso", "password": PASSWORD})

    assert status == 409


def test_setup_from_remote_address_is_refused(app):
    status, _ = Client(app, ip="203.0.113.9").post("/api/setup", {"username": "intruso", "password": PASSWORD})

    assert status == 403
    assert Client(app).get("/api/status")[1]["setup_required"] is True  # nada foi criado


def test_remote_setup_can_be_explicitly_allowed():
    app = WebApp(db_path=":memory:", secret=b"s" * 32, allow_remote_setup=True)

    assert Client(app, ip="203.0.113.9").post("/api/setup", {"username": "dono", "password": PASSWORD})[0] == 201


def test_login_wrong_password_is_401_and_generic(app, admin):
    status, body = Client(app).post("/api/login", {"username": "admin", "password": "errada-errada"})
    status2, body2 = Client(app).post("/api/login", {"username": "naoexiste", "password": "errada-errada"})

    assert status == status2 == 401
    assert body["message"] == body2["message"]


def test_login_is_throttled_after_repeated_failures():
    app = WebApp(db_path=":memory:", secret=b"s" * 32, throttle=LoginThrottle(max_failures=3))
    Client(app).post("/api/setup", {"username": "admin", "password": PASSWORD})
    client = Client(app)

    for _ in range(3):
        assert client.post("/api/login", {"username": "admin", "password": "errada-errada"})[0] == 401
    status, body = client.post("/api/login", {"username": "admin", "password": PASSWORD})

    assert status == 429
    assert body["error"] == "too_many_attempts"


# ---------------------------------------------------------------- autenticação e papéis


@pytest.mark.parametrize(
    "method,path",
    [("GET", "/api/products"), ("GET", "/api/dashboard"), ("POST", "/api/stock"), ("GET", "/api/users"), ("GET", "/api/export/products.csv")],
)
def test_protected_routes_require_login(app, admin, method, path):
    assert Client(app).call(method, path, {} if method == "POST" else None)[0] == 401


def test_garbage_token_is_401(app, admin):
    assert Client(app, "lixo.lixo").get("/api/products")[0] == 401


def test_viewer_can_read_but_not_write(app, admin):
    make_product(admin)
    viewer = make_user(app, admin, "leitor", "viewer")

    assert viewer.get("/api/products")[0] == 200
    assert viewer.post("/api/products", {"name": "X", "price": 1})[0] == 403
    assert viewer.post("/api/stock", {"product_id": 1, "type": "in", "quantity": 1})[0] == 403
    assert viewer.delete("/api/products/1")[0] == 403


def test_operator_cannot_manage_users(app, admin):
    operator = make_user(app, admin, "oper", "operator")

    assert operator.get("/api/users")[0] == 403
    assert operator.post("/api/users", {"username": "x1x", "password": PASSWORD, "role": "admin"})[0] == 403


def test_role_change_takes_effect_immediately(app, admin):
    operator = make_user(app, admin, "oper", "operator")
    op_id = next(u["id"] for u in admin.get("/api/users")[1]["users"] if u["username"] == "oper")
    assert operator.post("/api/products", {"name": "A", "price": 1})[0] == 201

    admin.patch(f"/api/users/{op_id}", {"role": "viewer"})

    assert operator.post("/api/products", {"name": "B", "price": 1})[0] == 403  # mesmo token antigo


def test_deleted_user_loses_access_immediately(app, admin):
    temp = make_user(app, admin, "temp", "operator")
    temp_id = next(u["id"] for u in admin.get("/api/users")[1]["users"] if u["username"] == "temp")

    admin.delete(f"/api/users/{temp_id}")

    assert temp.get("/api/products")[0] == 401


def test_admin_cannot_delete_self_or_last_admin(app, admin):
    me = admin.get("/api/me")[1]["user"]

    assert admin.delete(f"/api/users/{me['id']}")[0] == 422
    assert admin.patch(f"/api/users/{me['id']}", {"role": "viewer"})[0] == 409


def test_unknown_route_404_and_wrong_method_405(app, admin):
    assert admin.get("/api/nada")[0] == 404
    assert admin.call("PATCH", "/api/products")[0] == 405


# ---------------------------------------------------------------- produtos e estoque


def test_create_product_with_initial_stock_creates_history(admin):
    product = make_product(admin, stock=12)

    movements = admin.get("/api/movements")[1]["movements"]

    assert product["stock"] == 12
    assert [(m["type"], m["quantity"], m["reason"]) for m in movements] == [("in", 12, "Estoque inicial")]


def test_stock_in_out_adjustment_flow(admin):
    product = make_product(admin, stock=10)
    pid = product["id"]

    assert admin.post("/api/stock", {"product_id": pid, "type": "in", "quantity": 5})[1]["product"]["stock"] == 15
    assert admin.post("/api/stock", {"product_id": pid, "type": "out", "quantity": 3})[1]["product"]["stock"] == 12
    assert admin.post("/api/stock", {"product_id": pid, "type": "adjustment", "quantity": 7})[1]["product"]["stock"] == 7


def test_cannot_remove_more_than_available_and_nothing_is_recorded(admin):
    pid = make_product(admin, stock=2)["id"]

    status, body = admin.post("/api/stock", {"product_id": pid, "type": "out", "quantity": 3})
    movements = admin.get("/api/movements")[1]["movements"]

    assert status == 422 and body["details"]["estoque_atual"] == 2
    assert len(movements) == 1  # só o estoque inicial


@pytest.mark.parametrize(
    "payload",
    [
        {"product_id": 1, "type": "steal", "quantity": 1},
        {"product_id": 1, "type": "in", "quantity": 0},
        {"product_id": 1, "type": "in", "quantity": -4},
        {"product_id": 1, "type": "in", "quantity": 1.5},
        {"product_id": 1, "type": "in", "quantity": "10"},
        {"product_id": 1, "type": "in", "quantity": True},
        {"product_id": 1, "type": "in", "quantity": 10**12},
        {"product_id": "1", "type": "in", "quantity": 1},
        {"product_id": 1, "type": "in", "quantity": 1, "expiry_date": "amanhã"},
        {"type": "in", "quantity": 1},
    ],
)
def test_invalid_stock_payloads_are_422(admin, payload):
    make_product(admin)

    assert admin.post("/api/stock", payload)[0] == 422


def test_stock_for_unknown_product_is_404(admin):
    assert admin.post("/api/stock", {"product_id": 999, "type": "in", "quantity": 1})[0] == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "price": 1},
        {"name": "   ", "price": 1},
        {"name": "A" * 121, "price": 1},
        {"name": "A", "price": 0},
        {"name": "A", "price": -3},
        {"name": "A", "price": "10"},
        {"name": "A", "price": float("nan")},
        {"name": "A", "price": 1, "stock": -1},
        {"name": 123, "price": 1},
        {"price": 1},
    ],
)
def test_invalid_product_payloads_are_422(admin, payload):
    body = json.dumps(payload).encode()  # json.dumps aceita NaN; o servidor deve recusar

    assert Client(admin.app, admin.token).post("/api/products", body)[0] == 422


def test_duplicate_product_name_is_409(admin):
    make_product(admin, name="Caneca")

    assert admin.post("/api/products", {"name": "Caneca", "price": 5})[0] == 409


def test_failed_create_does_not_leave_orphan_movement(admin):
    make_product(admin, name="Caneca", stock=3)

    admin.post("/api/products", {"name": "Caneca", "price": 5, "stock": 9})  # duplicado

    assert len(admin.get("/api/movements")[1]["movements"]) == 1


def test_update_product_ignores_stock_field(admin):
    pid = make_product(admin, stock=5)["id"]

    product = admin.put(f"/api/products/{pid}", {"name": "Nova", "price": 12.5, "stock": 999})[1]["product"]

    assert (product["name"], product["price"], product["stock"]) == ("Nova", 12.5, 5)


def test_remove_product_without_history_deletes(admin):
    pid = make_product(admin, stock=0)["id"]

    assert admin.delete(f"/api/products/{pid}")[1]["result"] == "deleted"
    assert admin.get("/api/products")[1]["products"] == []


def test_remove_product_with_history_archives_and_keeps_history(admin):
    pid = make_product(admin, name="Caneca", stock=4)["id"]

    assert admin.delete(f"/api/products/{pid}")[1]["result"] == "archived"

    assert admin.get("/api/products")[1]["products"] == []
    assert len(admin.get("/api/movements")[1]["movements"]) == 1  # histórico intacto
    assert admin.post("/api/products", {"name": "Caneca", "price": 9})[0] == 201  # nome liberado


def test_remove_unknown_product_is_404(admin):
    assert admin.delete("/api/products/42")[0] == 404


def test_search_and_category_filters(admin):
    make_product(admin, name="Caneca azul", category="Casa")
    make_product(admin, name="Caderno", category="Papelaria")

    names = lambda q: [p["name"] for p in admin.get(q)[1]["products"]]

    assert names("/api/products?q=CANE") == ["Caneca azul"]
    assert names("/api/products?category=Papelaria") == ["Caderno"]


def test_dashboard_totals_and_alerts(admin):
    make_product(admin, name="Barato", price=2.0, stock=3)    # baixo
    make_product(admin, name="Caro", price=100.0, stock=10)
    make_product(admin, name="Zerado", price=1.0, stock=0)

    totals = admin.get("/api/dashboard")[1]["totals"]

    assert totals["products"] == 3 and totals["units"] == 13
    assert totals["stock_value"] == 1006.0
    assert totals["low_stock"] == 2 and totals["out_of_stock"] == 1


def test_expiring_batches_listed_and_zero_stock_hidden(admin):
    from datetime import date, timedelta

    soon = (date.today() + timedelta(days=10)).isoformat()
    a = make_product(admin, name="Com validade", stock=0)["id"]
    admin.post("/api/stock", {"product_id": a, "type": "in", "quantity": 5, "batch_number": "L1", "expiry_date": soon})
    b = make_product(admin, name="Vendido todo", stock=0)["id"]
    admin.post("/api/stock", {"product_id": b, "type": "in", "quantity": 2, "batch_number": "L2", "expiry_date": soon})
    admin.post("/api/stock", {"product_id": b, "type": "out", "quantity": 2})

    batches = admin.get("/api/expiring?days=30")[1]["batches"]

    assert [(x["product_name"], x["batch_number"], x["days_remaining"]) for x in batches] == [("Com validade", "L1", 10)]


# ---------------------------------------------------------------- clientes e usuários


def test_customer_crud(admin):
    _, data = admin.post("/api/customers", {"name": "Ana", "email": "ana@example.com"})
    cid = data["customer"]["id"]

    assert admin.put(f"/api/customers/{cid}", {"phone": "123"})[1]["customer"]["phone"] == "123"
    assert admin.get("/api/customers?q=ana")[1]["customers"][0]["name"] == "Ana"
    assert admin.delete(f"/api/customers/{cid}")[0] == 200
    assert admin.get("/api/customers")[1]["customers"] == []


def test_customer_invalid_email_is_422(admin):
    assert admin.post("/api/customers", {"name": "Ana", "email": "sem-arroba"})[0] == 422


def test_change_password_flow(app, admin):
    assert admin.post("/api/me/password", {"current_password": "errada-errada", "new_password": "nova-senha-9"})[0] == 403
    assert admin.post("/api/me/password", {"current_password": PASSWORD, "new_password": "nova-senha-9"})[0] == 200
    assert Client(app).post("/api/login", {"username": "admin", "password": "nova-senha-9"})[0] == 200


# ---------------------------------------------------------------- entrada hostil


@pytest.mark.parametrize("body", [b"{", b"[]", b'"texto"', b"\xff\xfe", b"null"])
def test_malformed_json_is_422(admin, body):
    assert Client(admin.app, admin.token).post("/api/products", body)[0] == 422


def test_oversized_body_is_rejected(admin):
    huge = json.dumps({"name": "A" * 100_000, "price": 1}).encode()

    assert Client(admin.app, admin.token).post("/api/products", huge)[0] == 422


def test_sql_injection_payload_is_just_text(admin):
    evil = "x'); DROP TABLE products;--"

    pid = make_product(admin, name=evil)["id"]

    assert admin.get(f"/api/products?q={'DROP'}")[1]["products"][0]["name"] == evil
    assert admin.get("/api/dashboard")[1]["totals"]["products"] == 1 and pid


def test_csv_export_neutralizes_formulas(admin):
    make_product(admin, name='=HYPERLINK("http://evil","clique")')

    response = admin.get("/api/export/products.csv")[1]
    text = response.body.decode("utf-8-sig")

    assert response.headers["Content-Type"].startswith("text/csv")
    assert "attachment" in response.headers["Content-Disposition"]
    assert "'=HYPERLINK" in text and ",=HYPERLINK" not in text


# ---------------------------------------------------------------- estáticos e cabeçalhos


def test_index_is_served_with_security_headers(app):
    response = app.handle("GET", "/", {}, b"", "127.0.0.1")

    assert response.status == 200 and b"<title>OpenOps</title>" in response.body
    assert "script-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


@pytest.mark.parametrize(
    "path",
    ["/static/../app.py", "/static/../../openops_core/db.py", "/static/%2e%2e/app.py", "/../etc/passwd", "/static/nada.js", "/static/", "/static/.."],
)
def test_static_path_traversal_is_blocked(app, path):
    assert app.handle("GET", path, {}, b"", "127.0.0.1").status == 404


def test_host_header_allowlist_blocks_dns_rebinding():
    app = WebApp(db_path=":memory:", secret=b"s" * 32, allowed_hosts=frozenset({"localhost", "127.0.0.1"}))

    assert app.handle("GET", "/api/health", {"Host": "localhost:8000"}, b"", "127.0.0.1").status == 200
    assert app.handle("GET", "/api/health", {"Host": "evil.example.com"}, b"", "127.0.0.1").status == 421


def test_errors_never_leak_stack_traces(admin, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("segredo interno /etc/shadow")

    monkeypatch.setattr(admin.app.products, "list_products", boom)

    status, body = admin.get("/api/products")

    assert status == 500
    assert "segredo" not in json.dumps(body) and "Traceback" not in json.dumps(body)


# ---------------------------------------------------------------- concorrência (bug real corrigido)


def test_concurrent_removals_never_oversell(admin):
    """Antes da correção, duas saídas simultâneas liam o mesmo saldo e uma
    sobrescrevia a outra, vendendo estoque que não existia."""
    pid = make_product(admin, stock=50)["id"]
    results = []

    def sell(_):
        status, _body = Client(admin.app, admin.token).post("/api/stock", {"product_id": pid, "type": "out", "quantity": 1})
        results.append(status)

    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(sell, range(120)))

    final = admin.get("/api/products")[1]["products"][0]["stock"]
    movements = admin.get(f"/api/movements?product_id={pid}&limit=1000")[1]["movements"]

    assert results.count(201) == 50
    assert results.count(422) == 70
    assert final == 0
    assert sum(1 for m in movements if m["type"] == "out") == 50
