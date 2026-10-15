# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""
openops_web.server
===================

Adaptador HTTP fino: traduz o protocolo (``http.server`` da biblioteca
padrão) para chamadas a :meth:`openops_web.app.WebApp.handle`. Toda a
lógica de negócio e de segurança vive em ``app.py``; aqui só há
transporte — por isso este arquivo é curto e quase não precisa de testes
além de um teste de integração com um socket real.

Por que ``http.server`` e não FastAPI/Flask? Zero dependências: quem
baixa o projeto roda ``python openops.py serve`` e pronto, sem
``pip install``, sem ambiente virtual — requisito central para um
sistema pensado para quem não programa.
"""

from __future__ import annotations

import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from openops_core.logging import LogCategory, get_logger

from .app import MAX_BODY_BYTES, WebApp

logger = get_logger("openops.web.server")

LOOPBACK_BIND_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
LOOPBACK_HOST_HEADERS = frozenset({"localhost", "127.0.0.1", "[::1]", "::1"})


class _Server(ThreadingHTTPServer):
    daemon_threads = True  # threads de requisição não seguram o encerramento
    allow_reuse_address = True


def _make_handler(app: WebApp) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        timeout = 15  # segundos: derruba conexões "penduradas" (slowloris)
        server_version = "OpenOps"
        sys_version = ""  # não anuncia a versão do Python

        def _serve(self) -> None:
            length_header = self.headers.get("Content-Length", "0")
            try:
                length = int(length_header)
            except ValueError:
                length = -1
            if length < 0 or length > MAX_BODY_BYTES:
                self._send(413, b'{"error":"payload_too_large","message":"requisi\xc3\xa7\xc3\xa3o grande demais","details":{}}',
                           {"Content-Type": "application/json; charset=utf-8"}, close=True)
                return
            body = self.rfile.read(length) if length else b""
            response = app.handle(
                self.command,
                self.path,
                {k: v for k, v in self.headers.items()},
                body,
                self.client_address[0],
            )
            self._send(response.status, response.body, response.headers, head_only=self.command == "HEAD")

        def _send(self, status: int, body: bytes, headers: dict[str, str], *, head_only: bool = False, close: bool = False) -> None:
            self.send_response(status)
            for name, value in headers.items():
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(body)))
            if close:
                self.send_header("Connection", "close")
                self.close_connection = True
            self.end_headers()
            if not head_only:
                self.wfile.write(body)

        do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = do_HEAD = _serve

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            logger.info("http", category=LogCategory.API, request=format % args, client=self.client_address[0])

    return Handler


def make_server(app: WebApp, host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    """Cria (sem iniciar) o servidor. ``port=0`` escolhe uma porta livre —
    usado pelos testes. Se ``host`` é local, ativa a checagem de ``Host``
    contra DNS rebinding.
    """
    if host in LOOPBACK_BIND_HOSTS and app.allowed_hosts is None:
        app.allowed_hosts = LOOPBACK_HOST_HEADERS
    return _Server((host, port), _make_handler(app))


def serve(app: WebApp, host: str = "127.0.0.1", port: int = 8000, *, open_browser: bool = False) -> None:
    server = make_server(app, host, port)
    actual_port = server.server_address[1]
    url = f"http://{'localhost' if host in LOOPBACK_BIND_HOSTS else host}:{actual_port}/"
    logger.info("servidor iniciado", category=LogCategory.API, url=url)
    print(f"\n  OpenOps rodando em {url}\n  Pressione Ctrl+C para encerrar.\n", flush=True)
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Encerrando...", flush=True)
    finally:
        server.server_close()
        app.close()
