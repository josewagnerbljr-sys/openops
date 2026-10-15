# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""
openops_web.app
================

O "cérebro" do micro-site: recebe uma requisição já decodificada
(método, caminho, cabeçalhos, corpo) e devolve uma resposta
(status, cabeçalhos, corpo) — **sem abrir socket nenhum**.

Separar isso do servidor HTTP (``openops_web.server``) é a decisão de
arquitetura mais importante deste módulo: todas as regras — autenticação,
papéis, validação, rotas — viram uma função pura de entrada→saída,
testável milhares de vezes por segundo sem rede. O servidor real é só um
adaptador fino por cima.

Uso de IA (política do CS50 para o projeto final): este módulo foi escrito com a
assistência da IA Claude (Anthropic). O problema e os requisitos são do autor do
projeto; a implementação foi escrita com a IA. Veja README.md, seção 6.
"""

from __future__ import annotations

import csv
import io
import json
import logging as _stdlib_logging
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlsplit

from openops_core.db import Database
from openops_core.errors import (
    AuthorizationError,
    NotFoundError,
    OpenOpsError,
    ValidationError,
    http_status_for,
)
from openops_core.logging import LogCategory, get_logger
from openops_core.registry import ModuleRegistry
from openops_core.roles import ROLE_LEVELS

from openops_business.customers.service import CustomerService
from openops_business.customers.service import register as register_customers
from openops_business.inventory.models import MOVEMENT_TYPES
from openops_business.inventory.service import (
    DEFAULT_EXPIRY_ALERT_DAYS,
    LOW_STOCK_THRESHOLD,
    InventoryService,
)
from openops_business.inventory.service import register as register_inventory
from openops_business.products.service import ProductService
from openops_business.products.service import register as register_products

from .security import (
    LoginThrottle,
    TokenSigner,
    UnauthenticatedError,
    load_or_create_secret,
)
from .users import UserStore, WebUser, validate_role

__version__ = "1.0.0"

logger = get_logger("openops.web")

MAX_BODY_BYTES = 64 * 1024
SESSION_TTL_SECONDS = 8 * 60 * 60
LOOPBACK_ADDRESSES = frozenset({"127.0.0.1", "::1", "::ffff:127.0.0.1"})

STATIC_DIR = Path(__file__).parent / "static"
STATIC_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}

#: Política de segurança de conteúdo: a página só pode carregar scripts,
#: estilos e imagens do próprio servidor — nada de CDN, nada de código
#: inline. Mesmo que um dado malicioso chegasse ao HTML, o navegador se
#: recusaria a executá-lo.
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Cross-Origin-Resource-Policy": "same-origin",
}


@dataclass
class Request:
    method: str
    path: str
    query: dict[str, list[str]] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)  # chaves em minúsculas
    body: bytes = b""
    client_ip: str = "127.0.0.1"

    def arg(self, name: str, default: str | None = None) -> str | None:
        values = self.query.get(name)
        return values[0] if values else default


@dataclass
class Response:
    status: int
    body: bytes = b""
    headers: dict[str, str] = field(default_factory=dict)


def _json(status: int, payload: Any, extra: dict[str, str] | None = None) -> Response:
    headers = {"Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store"}
    headers.update(extra or {})
    return Response(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers)


# --------------------------------------------------------------------------
# Validação de entrada. Toda entrada do navegador é tratada como hostil:
# tipo, tamanho e faixa são conferidos aqui, antes de tocar no domínio.
# --------------------------------------------------------------------------


def _text(data: dict, key: str, *, required: bool = False, max_len: int = 120, default: str = "") -> str:
    value = data.get(key, default)
    if value is None:
        value = default
    if not isinstance(value, str):
        raise ValidationError("dados inválidos", details={key: "deve ser texto"})
    value = value.strip()
    if required and not value:
        raise ValidationError("dados inválidos", details={key: "campo obrigatório"})
    if len(value) > max_len:
        raise ValidationError("dados inválidos", details={key: f"máximo de {max_len} caracteres"})
    return value


def _number(data: dict, key: str, *, minimum: float, maximum: float = 1_000_000_000) -> float:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError("dados inválidos", details={key: "deve ser um número"})
    if value != value or not (minimum <= value <= maximum):  # NaN-safe
        raise ValidationError("dados inválidos", details={key: f"deve estar entre {minimum} e {maximum}"})
    return float(value)


def _integer(data: dict, key: str, *, minimum: int, maximum: int = 1_000_000_000) -> int:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        else:
            raise ValidationError("dados inválidos", details={key: "deve ser um número inteiro"})
    if not (minimum <= value <= maximum):
        raise ValidationError("dados inválidos", details={key: f"deve estar entre {minimum} e {maximum}"})
    return value


def _optional_date(data: dict, key: str) -> date | None:
    raw = data.get(key)
    if raw in (None, ""):
        return None
    try:
        return date.fromisoformat(str(raw))
    except ValueError:
        raise ValidationError("dados inválidos", details={key: "use o formato AAAA-MM-DD"}) from None


_CSV_DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value: Any) -> Any:
    """Neutraliza "CSV/formula injection": um nome de produto como
    ``=HYPERLINK(...)`` viraria uma fórmula executável ao abrir o arquivo
    no Excel. Prefixar com apóstrofo faz a planilha tratar como texto.
    """
    if isinstance(value, str) and value.startswith(_CSV_DANGEROUS_PREFIXES):
        return "'" + value
    return value


def rows_to_csv(header: list[str], rows: list[list[Any]]) -> bytes:
    """CSV em UTF-8 **com BOM** (para o Excel acertar os acentos) e com
    células neutralizadas contra injeção de fórmula.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    for row in rows:
        writer.writerow([_csv_safe(cell) for cell in row])
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def _csv_response(filename: str, header: list[str], rows: list[list[Any]]) -> Response:
    return Response(
        200,
        rows_to_csv(header, rows),
        {
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


# --------------------------------------------------------------------------
# Aplicação
# --------------------------------------------------------------------------

Handler = Callable[["WebApp", Request, "WebUser | None", dict[str, str]], Any]


class WebApp:
    """Aplicação do micro-site. Uma instância = um banco + um conjunto de
    serviços; ``handle`` é thread-safe (a camada de banco serializa o acesso).
    """

    def __init__(
        self,
        *,
        db_path: str = ":memory:",
        secret: bytes | None = None,
        allow_remote_setup: bool = False,
        allowed_hosts: frozenset[str] | None = None,
        session_ttl_seconds: int = SESSION_TTL_SECONDS,
        throttle: LoginThrottle | None = None,
        static_dir: Path | None = None,
    ) -> None:
        self.db = Database(db_path)
        self.db.connect()

        registry = ModuleRegistry()  # isolado: cada app tem o seu
        self.products = ProductService(self.db)
        register_products(registry)
        self.customers = CustomerService(self.db)
        register_customers(registry)
        self.inventory = InventoryService(self.db, self.products)
        register_inventory(registry)
        self.registry = registry
        self.users = UserStore(self.db)

        if secret is None:
            secret_path = None if db_path == ":memory:" else f"{db_path}.secret"
            secret = load_or_create_secret(secret_path)
        self.signer = TokenSigner(secret)
        self.session_ttl_seconds = session_ttl_seconds
        self.throttle = throttle or LoginThrottle()
        self.allow_remote_setup = allow_remote_setup
        self.allowed_hosts = allowed_hosts
        self.static_dir = (static_dir or STATIC_DIR).resolve()

        self._routes: list[tuple[str, re.Pattern[str], Handler, str | None]] = []
        self._register_routes()

    def close(self) -> None:
        self.db.close()

    # -- roteamento --------------------------------------------------------

    def _route(self, method: str, pattern: str, handler: Handler, role: str | None) -> None:
        """``role=None`` → rota pública; senão, papel mínimo exigido."""
        regex = re.compile("^" + re.sub(r"\{(\w+)\}", r"(?P<\1>[0-9]+)", pattern) + "$")
        self._routes.append((method, regex, handler, role))

    def _register_routes(self) -> None:
        r = self._route
        r("GET", "/api/health", WebApp._health, None)
        r("GET", "/api/status", WebApp._status, None)
        r("POST", "/api/setup", WebApp._setup, None)
        r("POST", "/api/login", WebApp._login, None)
        r("GET", "/api/me", WebApp._me, "viewer")
        r("POST", "/api/me/password", WebApp._change_password, "viewer")
        r("GET", "/api/dashboard", WebApp._dashboard, "viewer")

        r("GET", "/api/products", WebApp._list_products, "viewer")
        r("POST", "/api/products", WebApp._create_product, "operator")
        r("PUT", "/api/products/{id}", WebApp._update_product, "operator")
        r("DELETE", "/api/products/{id}", WebApp._remove_product, "operator")

        r("POST", "/api/stock", WebApp._move_stock, "operator")
        r("GET", "/api/movements", WebApp._list_movements, "viewer")
        r("GET", "/api/expiring", WebApp._expiring, "viewer")

        r("GET", "/api/customers", WebApp._list_customers, "viewer")
        r("POST", "/api/customers", WebApp._create_customer, "operator")
        r("PUT", "/api/customers/{id}", WebApp._update_customer, "operator")
        r("DELETE", "/api/customers/{id}", WebApp._delete_customer, "operator")

        r("GET", "/api/users", WebApp._list_users, "admin")
        r("POST", "/api/users", WebApp._create_user, "admin")
        r("PATCH", "/api/users/{id}", WebApp._update_user, "admin")
        r("DELETE", "/api/users/{id}", WebApp._delete_user, "admin")

        r("GET", "/api/export/products.csv", WebApp._export_products, "viewer")
        r("GET", "/api/export/movements.csv", WebApp._export_movements, "viewer")

    # -- ponto de entrada --------------------------------------------------

    def handle(
        self,
        method: str,
        target: str,
        headers: dict[str, str] | None = None,
        body: bytes = b"",
        client_ip: str = "127.0.0.1",
    ) -> Response:
        """Processa uma requisição. Nunca levanta exceção: qualquer falha
        vira uma resposta JSON com o status HTTP adequado.
        """
        parts = urlsplit(target)
        request = Request(
            method=method.upper(),
            path=parts.path,
            query=parse_qs(parts.query, keep_blank_values=True),
            headers={k.lower(): v for k, v in (headers or {}).items()},
            body=body,
            client_ip=client_ip,
        )
        try:
            response = self._dispatch(request)
        except OpenOpsError as exc:
            response = self._error_response(exc)
        except Exception:  # noqa: BLE001 - última barreira: nunca vazar stack trace ao cliente
            _stdlib_logging.getLogger("openops.web").exception(
                "erro inesperado em %s %s", request.method, request.path
            )
            response = _json(
                500, {"error": "internal_error", "message": "erro interno; tente novamente", "details": {}}
            )

        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        return response

    def _error_response(self, exc: OpenOpsError) -> Response:
        status = 401 if isinstance(exc, UnauthenticatedError) else http_status_for(exc)
        return _json(status, exc.to_dict())

    def _dispatch(self, request: Request) -> Response:
        if self.allowed_hosts is not None:
            host = request.headers.get("host", "")
            hostname = host.rsplit(":", 1)[0] if not host.endswith("]") else host
            if hostname.lower() not in self.allowed_hosts:
                # Defesa contra DNS rebinding: um site malicioso não consegue
                # fazer o navegador do usuário falar com este servidor local
                # usando um nome de domínio qualquer.
                return _json(421, {"error": "invalid_host", "message": "host não permitido", "details": {}})

        if not request.path.startswith("/api/"):
            return self._static(request)

        for method, regex, handler, role in self._routes:
            match = regex.match(request.path)
            if match is None:
                continue
            if method != request.method:
                continue
            user = self._authenticate(request) if role is not None else None
            if role is not None and ROLE_LEVELS[user.role] < ROLE_LEVELS[role]:
                raise AuthorizationError(
                    f"esta ação exige o papel '{role}' ou superior",
                    details={"seu_papel": user.role, "papel_exigido": role},
                )
            result = handler(self, request, user, match.groupdict())
            if isinstance(result, Response):
                return result
            status, payload = result
            return _json(status, payload)

        known_path = any(regex.match(request.path) for _, regex, _, _ in self._routes)
        if known_path:
            return _json(405, {"error": "method_not_allowed", "message": "método não permitido", "details": {}})
        raise NotFoundError("rota não encontrada")

    def _authenticate(self, request: Request) -> WebUser:
        header = request.headers.get("authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise UnauthenticatedError("faça login para continuar")
        username = self.signer.verify(token.strip())
        user = self.users.get_by_username(username)
        if user is None:
            raise UnauthenticatedError("sessão inválida, entre novamente")
        return user

    def _json_body(self, request: Request) -> dict[str, Any]:
        if len(request.body) > MAX_BODY_BYTES:
            raise ValidationError("requisição grande demais")
        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValidationError("o corpo da requisição não é um JSON válido") from None
        if not isinstance(data, dict):
            raise ValidationError("o corpo da requisição deve ser um objeto JSON")
        return data

    def _audit(self, user: WebUser | None, action: str, **fields: Any) -> None:
        logger.info(
            action,
            category=LogCategory.SECURITY if action.startswith(("login", "user", "setup", "password")) else LogCategory.BUSINESS,
            user=user.username if user else None,
            **fields,
        )

    # -- arquivos estáticos ------------------------------------------------

    def _static(self, request: Request) -> Response:
        if request.method not in ("GET", "HEAD"):
            return _json(405, {"error": "method_not_allowed", "message": "método não permitido", "details": {}})

        path = "/index.html" if request.path in ("/", "") else request.path
        if path.startswith("/static/"):
            path = path[len("/static") :]
        candidate = (self.static_dir / path.lstrip("/")).resolve()
        # Bloqueio de path traversal: o arquivo resolvido TEM que estar dentro
        # da pasta static (cobre "../", links simbólicos e "%2e%2e").
        if not candidate.is_relative_to(self.static_dir) or not candidate.is_file():
            return _json(404, {"error": "not_found", "message": "página não encontrada", "details": {}})
        content_type = STATIC_TYPES.get(candidate.suffix.lower())
        if content_type is None:
            return _json(404, {"error": "not_found", "message": "página não encontrada", "details": {}})
        return Response(200, candidate.read_bytes(), {"Content-Type": content_type, "Cache-Control": "no-cache"})

    # -- handlers: meta e sessão ------------------------------------------

    def _health(self, request: Request, user: WebUser | None, params: dict[str, str]):
        return 200, {"status": "ok"}

    def _status(self, request: Request, user: WebUser | None, params: dict[str, str]):
        return 200, {
            "app": "OpenOps",
            "version": __version__,
            "setup_required": self.users.count() == 0,
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
            "modules": [m.name for m in self.registry.list()],
        }

    def _session_payload(self, user: WebUser) -> dict[str, Any]:
        token = self.signer.issue(user.username, ttl_seconds=self.session_ttl_seconds)
        return {"token": token, "expires_in": self.session_ttl_seconds, "user": user.to_dict()}

    def _setup(self, request: Request, user: WebUser | None, params: dict[str, str]):
        if request.client_ip not in LOOPBACK_ADDRESSES and not self.allow_remote_setup:
            # Quem acessa primeiro a tela de configuração vira admin. Por isso
            # ela só funciona a partir da própria máquina — senão, num servidor
            # exposto, o primeiro visitante da internet viraria o dono.
            raise AuthorizationError(
                "a configuração inicial só pode ser feita a partir do próprio computador do servidor "
                "(ou use: python openops.py init)"
            )
        data = self._json_body(request)
        admin = self.users.create_first_admin(
            username=_text(data, "username", required=True, max_len=32),
            password=_text_raw(data, "password"),
        )
        self._audit(admin, "setup.completed", ip=request.client_ip)
        return 201, self._session_payload(admin)

    def _login(self, request: Request, user: WebUser | None, params: dict[str, str]):
        data = self._json_body(request)
        username = data.get("username")
        password = data.get("password")
        key = f"{request.client_ip}|{str(username).lower()}"

        wait = self.throttle.retry_after(key)
        if wait:
            response = _json(
                429,
                {
                    "error": "too_many_attempts",
                    "message": f"muitas tentativas; aguarde {wait} segundos",
                    "details": {"retry_after": wait},
                },
                {"Retry-After": str(wait)},
            )
            self._audit(None, "login.blocked", username=str(username)[:32], ip=request.client_ip)
            return response

        try:
            authenticated = self.users.authenticate(username=username, password=password)
        except AuthorizationError:
            self.throttle.record_failure(key)
            self._audit(None, "login.failed", username=str(username)[:32], ip=request.client_ip)
            raise
        self.throttle.reset(key)
        self._audit(authenticated, "login.ok", ip=request.client_ip)
        return 200, self._session_payload(authenticated)

    def _me(self, request: Request, user: WebUser, params: dict[str, str]):
        return 200, {"user": user.to_dict()}

    def _change_password(self, request: Request, user: WebUser, params: dict[str, str]):
        data = self._json_body(request)
        self.users.change_password(
            user.id,
            current_password=_text_raw(data, "current_password"),
            new_password=_text_raw(data, "new_password"),
        )
        self._audit(user, "password.changed")
        return 200, {"ok": True}

    # -- handlers: painel --------------------------------------------------

    def _dashboard(self, request: Request, user: WebUser, params: dict[str, str]):
        products = self.products.list_products()
        by_id = {p.id: p for p in products}
        low = [p for p in products if p.stock <= LOW_STOCK_THRESHOLD]
        expiring = self._expiring_view(DEFAULT_EXPIRY_ALERT_DAYS, by_id)
        recent = self.inventory.list_movements()[:8]
        return 200, {
            "totals": {
                "products": len(products),
                "units": sum(p.stock for p in products),
                "stock_value": round(sum(p.price * p.stock for p in products), 2),
                "low_stock": len(low),
                "out_of_stock": sum(1 for p in products if p.stock == 0),
                "expiring_soon": len(expiring),
            },
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
            "low_stock": [_product_dict(p) for p in sorted(low, key=lambda p: (p.stock, p.name))[:10]],
            "expiring": expiring[:10],
            "recent_movements": [self._movement_dict(m) for m in recent],
        }

    # -- handlers: produtos ------------------------------------------------

    def _list_products(self, request: Request, user: WebUser, params: dict[str, str]):
        category = request.arg("category") or None
        products = self.products.list_products(category=category)
        query = (request.arg("q") or "").strip().lower()
        if query:
            products = [p for p in products if query in p.name.lower() or query in p.category.lower()]
        return 200, {
            "products": [_product_dict(p) for p in products],
            "categories": sorted({p.category for p in self.products.list_products() if p.category}),
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
        }

    def _create_product(self, request: Request, user: WebUser, params: dict[str, str]):
        data = self._json_body(request)
        name = _text(data, "name", required=True)
        price = _number(data, "price", minimum=0.01)
        category = _text(data, "category", max_len=60)
        initial = _integer(data, "stock", minimum=0) if data.get("stock") not in (None, "") else 0

        # Produto + estoque inicial na MESMA transação, e o estoque inicial
        # entra como movimentação "in" — assim o histórico explica de onde
        # veio cada unidade, em vez de um saldo "caído do céu".
        with self.db.transaction():
            product = self.products.create_product(name=name, price=price, stock=0, category=category)
            if initial > 0:
                self.inventory.register_movement(
                    product_id=product.id, movement_type="in", quantity=initial, reason="Estoque inicial"
                )
        product = self.products.get_product(product.id)
        self._audit(user, "product.created", product_id=product.id, name=product.name)
        return 201, {"product": _product_dict(product)}

    def _update_product(self, request: Request, user: WebUser, params: dict[str, str]):
        data = self._json_body(request)
        changes: dict[str, Any] = {}
        if "name" in data:
            changes["name"] = _text(data, "name", required=True)
        if "price" in data:
            changes["price"] = _number(data, "price", minimum=0.01)
        if "category" in data:
            changes["category"] = _text(data, "category", max_len=60)
        # "stock" é ignorado de propósito: o saldo só muda por movimentação,
        # nunca por edição direta — é isso que mantém o histórico confiável.
        product = self.products.update_product(int(params["id"]), **changes)
        self._audit(user, "product.updated", product_id=product.id, fields=sorted(changes))
        return 200, {"product": _product_dict(product)}

    def _remove_product(self, request: Request, user: WebUser, params: dict[str, str]):
        product_id = int(params["id"])
        name = self.products.get_product(product_id).name
        result = self.products.remove_product(product_id)
        self._audit(user, "product.removed", product_id=product_id, name=name, result=result)
        return 200, {"result": result}

    # -- handlers: estoque -------------------------------------------------

    def _move_stock(self, request: Request, user: WebUser, params: dict[str, str]):
        data = self._json_body(request)
        movement_type = data.get("type")
        if movement_type not in MOVEMENT_TYPES:
            raise ValidationError("dados inválidos", details={"type": f"use um de {sorted(MOVEMENT_TYPES)}"})
        product_id = _integer(data, "product_id", minimum=1)
        quantity = _integer(data, "quantity", minimum=0 if movement_type == "adjustment" else 1)
        movement = self.inventory.register_movement(
            product_id=product_id,
            movement_type=movement_type,
            quantity=quantity,
            reason=_text(data, "reason", max_len=200),
            batch_number=_text(data, "batch_number", max_len=60),
            expiry_date=_optional_date(data, "expiry_date") if movement_type == "in" else None,
        )
        product = self.products.get_product(product_id)
        self._audit(user, "stock.moved", product_id=product_id, type=movement_type, quantity=quantity, new_stock=product.stock)
        return 201, {"movement": self._movement_dict(movement), "product": _product_dict(product)}

    def _list_movements(self, request: Request, user: WebUser, params: dict[str, str]):
        product_id = None
        if request.arg("product_id"):
            product_id = _integer({"v": _to_int(request.arg("product_id"))}, "v", minimum=1)
        limit = min(max(_to_int(request.arg("limit", "200")), 1), 1000)
        movements = self.inventory.list_movements(product_id=product_id)[:limit]
        return 200, {"movements": [self._movement_dict(m) for m in movements]}

    def _expiring(self, request: Request, user: WebUser, params: dict[str, str]):
        days = min(max(_to_int(request.arg("days", str(DEFAULT_EXPIRY_ALERT_DAYS))), 1), 3650)
        by_id = {p.id: p for p in self.products.list_products()}
        return 200, {"days": days, "batches": self._expiring_view(days, by_id)}

    def _expiring_view(self, days: int, by_id: dict[int, Any]) -> list[dict[str, Any]]:
        today = date.today()
        rows = []
        for m in self.inventory.expiring_batches(within_days=days):
            product = by_id.get(m.product_id)
            if product is None or product.stock == 0:
                continue  # produto arquivado ou sem saldo: nada a vencer na prateleira
            rows.append(
                {
                    "product_id": m.product_id,
                    "product_name": product.name,
                    "batch_number": m.batch_number,
                    "expiry_date": m.expiry_date.isoformat(),
                    "days_remaining": (m.expiry_date - today).days,
                    "received_quantity": m.quantity,
                    "current_stock": product.stock,
                }
            )
        return rows

    def _movement_dict(self, m: Any) -> dict[str, Any]:
        try:
            name = self.products.get_product(m.product_id).name
        except NotFoundError:  # pragma: no cover - FK impede, defesa em profundidade
            name = f"#{m.product_id}"
        return {
            "id": m.id,
            "product_id": m.product_id,
            "product_name": name,
            "type": m.movement_type,
            "quantity": m.quantity,
            "reason": m.reason,
            "batch_number": m.batch_number,
            "expiry_date": m.expiry_date.isoformat() if m.expiry_date else None,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }

    # -- handlers: clientes ------------------------------------------------

    def _list_customers(self, request: Request, user: WebUser, params: dict[str, str]):
        customers = self.customers.list_customers(search=(request.arg("q") or None))
        return 200, {"customers": [_customer_dict(c) for c in customers]}

    def _create_customer(self, request: Request, user: WebUser, params: dict[str, str]):
        data = self._json_body(request)
        customer = self.customers.create_customer(
            name=_text(data, "name", required=True),
            email=_text(data, "email", max_len=120) or None,
            phone=_text(data, "phone", max_len=40) or None,
            document=_text(data, "document", max_len=40) or None,
        )
        self._audit(user, "customer.created", customer_id=customer.id)
        return 201, {"customer": _customer_dict(customer)}

    def _update_customer(self, request: Request, user: WebUser, params: dict[str, str]):
        data = self._json_body(request)
        changes = {}
        if "name" in data:
            changes["name"] = _text(data, "name", required=True)
        for key, limit in (("email", 120), ("phone", 40), ("document", 40)):
            if key in data and _text(data, key, max_len=limit):
                changes[key] = _text(data, key, max_len=limit)
        customer = self.customers.update_customer(int(params["id"]), **changes)
        self._audit(user, "customer.updated", customer_id=customer.id)
        return 200, {"customer": _customer_dict(customer)}

    def _delete_customer(self, request: Request, user: WebUser, params: dict[str, str]):
        self.customers.delete_customer(int(params["id"]))
        self._audit(user, "customer.deleted", customer_id=int(params["id"]))
        return 200, {"result": "deleted"}

    # -- handlers: usuários (admin) ---------------------------------------

    def _list_users(self, request: Request, user: WebUser, params: dict[str, str]):
        return 200, {"users": [u.to_dict() for u in self.users.list()]}

    def _create_user(self, request: Request, user: WebUser, params: dict[str, str]):
        data = self._json_body(request)
        created = self.users.create(
            username=_text(data, "username", required=True, max_len=32),
            password=_text_raw(data, "password"),
            role=validate_role(data.get("role", "viewer")),
        )
        self._audit(user, "user.created", target=created.username, role=created.role)
        return 201, {"user": created.to_dict()}

    def _update_user(self, request: Request, user: WebUser, params: dict[str, str]):
        data = self._json_body(request)
        updated = self.users.set_role(int(params["id"]), validate_role(data.get("role")))
        self._audit(user, "user.role_changed", target=updated.username, role=updated.role)
        return 200, {"user": updated.to_dict()}

    def _delete_user(self, request: Request, user: WebUser, params: dict[str, str]):
        target = self.users.get(int(params["id"]))
        if target.id == user.id:
            raise ValidationError("você não pode apagar o próprio usuário", details={"id": target.id})
        self.users.delete(target.id)
        self._audit(user, "user.deleted", target=target.username)
        return 200, {"result": "deleted"}

    # -- handlers: exportação ---------------------------------------------

    PRODUCTS_CSV_HEADER = ["id", "nome", "categoria", "preco", "estoque", "valor_em_estoque"]
    MOVEMENTS_CSV_HEADER = ["data", "produto", "tipo", "quantidade", "motivo", "lote", "validade"]

    def products_table(self) -> list[list[Any]]:
        """Linhas do relatório de produtos (também usado pelo comando ``export`` da CLI)."""
        return [
            [p.id, p.name, p.category, f"{p.price:.2f}", p.stock, f"{p.price * p.stock:.2f}"]
            for p in self.products.list_products()
        ]

    def movements_table(self) -> list[list[Any]]:
        rows = []
        for m in self.inventory.list_movements():
            d = self._movement_dict(m)
            rows.append(
                [d["created_at"], d["product_name"], d["type"], d["quantity"], d["reason"], d["batch_number"], d["expiry_date"] or ""]
            )
        return rows

    def _export_products(self, request: Request, user: WebUser, params: dict[str, str]):
        return _csv_response("produtos.csv", self.PRODUCTS_CSV_HEADER, self.products_table())

    def _export_movements(self, request: Request, user: WebUser, params: dict[str, str]):
        return _csv_response("movimentacoes.csv", self.MOVEMENTS_CSV_HEADER, self.movements_table())


# --------------------------------------------------------------------------
# Serialização
# --------------------------------------------------------------------------


def _text_raw(data: dict, key: str) -> str:
    """Como ``_text`` mas SEM ``strip``: espaços em senhas são legítimos."""
    value = data.get(key)
    if not isinstance(value, str):
        raise ValidationError("dados inválidos", details={key: "campo obrigatório"})
    return value


def _to_int(value: str | None) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise ValidationError("parâmetro inválido", details={"query": "deve ser um número inteiro"}) from None


def _product_dict(p: Any) -> dict[str, Any]:
    return {
        "id": p.id,
        "name": p.name,
        "price": p.price,
        "stock": p.stock,
        "category": p.category,
        "low_stock": p.stock <= LOW_STOCK_THRESHOLD,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


def _customer_dict(c: Any) -> dict[str, Any]:
    return {"id": c.id, "name": c.name, "email": c.email, "phone": c.phone, "document": c.document}
