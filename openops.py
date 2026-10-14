#!/usr/bin/env python3
# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""
openops.py — ponto de entrada (CLI router) do OpenOps.

Este arquivo NÃO faz o trabalho pesado. Ele só:

1. lê os argumentos da linha de comando (``argparse``);
2. valida o que o usuário digitou;
3. carrega a configuração (arquivo JSON + variáveis de ambiente);
4. chama o módulo certo (``openops_web``, ``openops_business``, ``openops_core``).

Uso rápido::

    python openops.py init --admin jose --demo   # cria banco, admin e dados de exemplo
    python openops.py serve --open               # sobe o micro-site e abre o navegador
    python openops.py expiry --days 30           # lista lotes perto do vencimento
    python openops.py export products -o produtos.csv

Uso de IA (política do CS50 para o projeto final): este arquivo foi escrito com a
assistência da IA Claude (Anthropic). O problema e os requisitos são do autor do
projeto; a implementação foi escrita com a IA. Veja README.md, seção 6.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from pathlib import Path

# Os pacotes Python do projeto moram em ./python — adicioná-los ao caminho de
# importação permite rodar `python openops.py ...` direto do clone do
# repositório, sem `pip install` e sem configurar nada.
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

from openops_core import __version__ as CORE_VERSION  # noqa: E402
from openops_core.config import ConfigError, load_config  # noqa: E402
from openops_core.errors import ConfigurationError, OpenOpsError  # noqa: E402
from openops_core.logging import LogCategory, configure_logging, get_logger  # noqa: E402

DEFAULT_CONFIG_FILE = "openops.config.json"
DEFAULT_DB = "openops.db"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
LOG_FILE = "openops.log"

CONFIG_TEMPLATE = {
    "environment": "development",
    "log_level": "INFO",
    "db_path": DEFAULT_DB,
    "host": DEFAULT_HOST,
    "port": DEFAULT_PORT,
}

logger = get_logger("openops.cli")


# --------------------------------------------------------------------------
# Configuração: flag da linha de comando > variável de ambiente > arquivo > padrão
# --------------------------------------------------------------------------


def resolve_settings(args: argparse.Namespace) -> dict:
    """Combina as fontes de configuração na ordem de prioridade documentada.

    Levanta :class:`ConfigurationError` com uma mensagem clara quando um
    valor é inválido (ex.: porta que não é número) — nunca um traceback.
    """
    config_path = Path(args.config) if args.config else Path(DEFAULT_CONFIG_FILE)
    cfg = load_config(config_path if config_path.exists() else None)
    extra = cfg.extra

    port_raw = getattr(args, "port", None) or extra.get("port") or DEFAULT_PORT
    try:
        port = int(port_raw)
    except (TypeError, ValueError):
        raise ConfigurationError(f"porta inválida: {port_raw!r} (use um número de 1 a 65535)") from None
    if not 0 <= port <= 65535:
        raise ConfigurationError(f"porta fora do intervalo permitido: {port}")

    return {
        "db_path": args.db or extra.get("db_path") or cfg.database_url or DEFAULT_DB,
        "host": getattr(args, "host", None) or extra.get("host") or DEFAULT_HOST,
        "port": port,
        "log_level": (args.log_level or cfg.log_level or "INFO").upper(),
        "environment": cfg.environment,
    }


def build_app(settings: dict, **kwargs):
    # Import tardio: `--help` e `version` respondem instantaneamente e nunca
    # falham por causa de um módulo de negócio.
    from openops_web import WebApp

    return WebApp(db_path=settings["db_path"], **kwargs)


# --------------------------------------------------------------------------
# Comandos
# --------------------------------------------------------------------------


def cmd_init(args: argparse.Namespace, settings: dict) -> int:
    """Prepara uma instalação nova: configuração, banco e (opcional) admin."""
    config_path = Path(args.config) if args.config else Path(DEFAULT_CONFIG_FILE)
    if config_path.exists():
        print(f"✓ Configuração já existe: {config_path}")
    else:
        config_path.write_text(json.dumps(CONFIG_TEMPLATE, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"✓ Configuração criada: {config_path}")

    app = build_app(settings)
    try:
        print(f"✓ Banco de dados pronto: {settings['db_path']}")

        if args.admin:
            if app.users.count() > 0:
                print("• Já existe um administrador; nenhum usuário novo foi criado.")
            else:
                password = os.environ.get("OPENOPS_ADMIN_PASSWORD") or _ask_password()
                app.users.create_first_admin(username=args.admin, password=password)
                logger.info("administrador criado via CLI", category=LogCategory.SECURITY, username=args.admin)
                print(f"✓ Administrador '{args.admin}' criado.")
        elif app.users.count() == 0:
            print("• Nenhum usuário ainda: abra o micro-site no próprio computador para criar o administrador,")
            print("  ou rode:  python openops.py init --admin SEU_USUARIO")

        if args.demo:
            from openops_web.demo import seed_demo

            created = seed_demo(app)
            print("✓ Dados de demonstração criados." if created else "• Já existem produtos; demonstração ignorada.")
    finally:
        app.close()

    print("\nPróximo passo:  python openops.py serve --open")
    return 0


def _ask_password() -> str:
    while True:
        first = getpass.getpass("Senha do administrador (mín. 8 caracteres): ")
        if first != getpass.getpass("Repita a senha: "):
            print("As senhas não são iguais. Tente de novo.")
            continue
        return first


def cmd_serve(args: argparse.Namespace, settings: dict) -> int:
    from openops_web.server import serve

    if settings["host"] not in ("127.0.0.1", "localhost", "::1"):
        print(
            "⚠  Atenção: o servidor ficará acessível pela rede. Use apenas em redes de confiança "
            "ou atrás de HTTPS (proxy reverso).",
            file=sys.stderr,
        )

    app = build_app(settings, allow_remote_setup=args.allow_remote_setup)
    if args.demo:
        from openops_web.demo import seed_demo

        seed_demo(app)
    try:
        serve(app, settings["host"], settings["port"], open_browser=args.open)
    except OSError as exc:
        app.close()
        raise ConfigurationError(
            f"não foi possível usar {settings['host']}:{settings['port']} ({exc.strerror or exc}). "
            "A porta já está em uso? Tente: python openops.py serve --port 8080"
        ) from exc
    return 0


def cmd_expiry(args: argparse.Namespace, settings: dict) -> int:
    """Lista lotes perto do vencimento — pensado para agendadores (cron, Tarefas do Windows)."""
    app = build_app(settings)
    try:
        by_id = {p.id: p for p in app.products.list_products()}
        rows = app._expiring_view(args.days, by_id)  # mesma regra do painel
    finally:
        app.close()

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif not rows:
        print(f"Nenhum lote vence nos próximos {args.days} dias.")
    else:
        for r in rows:
            status = "VENCIDO" if r["days_remaining"] < 0 else f"{r['days_remaining']} dias"
            print(f"{r['expiry_date']}  {status:>9}  {r['product_name']}  (lote {r['batch_number'] or '-'})")
    # Código de saída 1 quando há lotes: permite `if python openops.py expiry; then ...` em scripts.
    return 1 if rows and args.fail_on_found else 0


def cmd_export(args: argparse.Namespace, settings: dict) -> int:
    from openops_web.app import WebApp, rows_to_csv

    app = build_app(settings)
    try:
        if args.what == "products":
            data = rows_to_csv(WebApp.PRODUCTS_CSV_HEADER, app.products_table())
        else:
            data = rows_to_csv(WebApp.MOVEMENTS_CSV_HEADER, app.movements_table())
    finally:
        app.close()
    out = Path(args.output or f"{args.what}.csv")
    out.write_bytes(data)
    print(f"✓ Arquivo gerado: {out}")
    return 0


def cmd_reset_password(args: argparse.Namespace, settings: dict) -> int:
    """Saída para "esqueci a senha": quem tem acesso ao computador redefine."""
    app = build_app(settings)
    try:
        password = os.environ.get("OPENOPS_NEW_PASSWORD") or _ask_password()
        app.users.reset_password(args.username, password)
        logger.info("senha redefinida via CLI", category=LogCategory.SECURITY, username=args.username)
    finally:
        app.close()
    print(f"✓ Senha de '{args.username}' redefinida.")
    return 0


def cmd_version(args: argparse.Namespace, settings: dict) -> int:
    from openops_web import __version__ as web_version

    print(f"OpenOps web {web_version} (core {CORE_VERSION}) — Python {sys.version.split()[0]}")
    return 0


# --------------------------------------------------------------------------
# Roteador
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openops.py",
        description="OpenOps — controle de estoque e operação no navegador, sem precisar programar.",
        epilog="Exemplo completo:  python openops.py init --admin jose --demo && python openops.py serve --open",
    )
    parser.add_argument("--config", help=f"arquivo de configuração JSON (padrão: {DEFAULT_CONFIG_FILE}, se existir)")
    parser.add_argument("--db", help=f"arquivo do banco SQLite (padrão: {DEFAULT_DB})")
    parser.add_argument("-v", "--verbose", action="store_true", help="mostra no terminal também os logs informativos (o arquivo openops.log sempre os recebe)")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], type=str.upper)
    sub = parser.add_subparsers(dest="command", metavar="comando", required=True)

    p = sub.add_parser("init", help="prepara banco, configuração e administrador")
    p.add_argument("--admin", metavar="USUARIO", help="cria o administrador (a senha é pedida de forma segura)")
    p.add_argument("--demo", action="store_true", help="carrega produtos e clientes de exemplo")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("serve", help="sobe o micro-site")
    p.add_argument("--host", help=f"endereço (padrão: {DEFAULT_HOST}, só este computador)")
    p.add_argument("--port", type=int, help=f"porta (padrão: {DEFAULT_PORT})")
    p.add_argument("--open", action="store_true", help="abre o navegador automaticamente")
    p.add_argument("--demo", action="store_true", help="carrega dados de exemplo se o banco estiver vazio")
    p.add_argument("--allow-remote-setup", action="store_true", help="permite criar o 1º admin por outro computador (inseguro)")
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("expiry", help="lista lotes perto do vencimento")
    p.add_argument("--days", type=_positive_int, default=30, help="janela em dias (padrão: 30)")
    p.add_argument("--json", action="store_true", help="saída em JSON")
    p.add_argument("--fail-on-found", action="store_true", help="sai com código 1 se houver lotes (para scripts)")
    p.set_defaults(func=cmd_expiry)

    p = sub.add_parser("export", help="exporta produtos ou movimentações para CSV")
    p.add_argument("what", choices=["products", "movements"])
    p.add_argument("-o", "--output", help="arquivo de saída")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("reset-password", help="redefine a senha de um usuário (esqueci a senha)")
    p.add_argument("username")
    p.set_defaults(func=cmd_reset_password)

    p = sub.add_parser("version", help="mostra as versões")
    p.set_defaults(func=cmd_version)
    return parser


def _positive_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{text}' não é um número inteiro") from None
    if value < 1:
        raise argparse.ArgumentTypeError("use um número maior que zero")
    return value


def _quiet_console(*, verbose: bool) -> None:
    """O arquivo ``openops.log`` guarda tudo (auditoria); o terminal só mostra
    avisos e erros, para não afogar quem usa o sistema em linhas de JSON.
    """
    import logging

    for handler in logging.getLogger().handlers:
        if not isinstance(handler, logging.FileHandler):
            handler.setLevel(logging.INFO if verbose else logging.WARNING)


def _force_utf8_output() -> None:
    """No Git Bash/PowerShell do Windows o Python costuma usar cp1252 quando a
    saída não é um console "puro", e imprimir "✓" ou "ç" derrubava o programa
    com ``UnicodeEncodeError`` (bug real, reproduzido com PYTHONIOENCODING=cp1252).
    Forçamos UTF-8 e, na pior hipótese, trocamos o caractere por "?" em vez de quebrar.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):  # pragma: no cover - stream especial
                pass


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    args = build_parser().parse_args(argv)
    try:
        settings = resolve_settings(args)
        configure_logging(settings["log_level"], log_file=LOG_FILE)
        _quiet_console(verbose=args.verbose)
        return args.func(args, settings)
    except (OpenOpsError, ConfigError) as exc:
        logger.error(exc.message, category=LogCategory.CORE, error=getattr(exc, "code", "error"))
        print(f"Erro: {exc.message}", file=sys.stderr)
        for key, value in exc.details.items():
            print(f"  - {key}: {value}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrompido.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
