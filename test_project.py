# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""
test_project.py — testes do ponto de entrada ``openops.py`` (CLI).

Rode da raiz do projeto:  python -m pytest test_project.py
Os testes do restante do sistema ficam em python/*/tests (veja README).
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import openops  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_cwd(tmp_path, monkeypatch):
    """Cada teste roda numa pasta vazia: nenhum banco/log de verdade é tocado."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENOPS_SECRET", raising=False)
    return tmp_path


def run(*argv):
    return openops.main(list(argv))


def test_version_prints_and_succeeds(capsys):
    assert run("version") == 0
    assert "OpenOps web" in capsys.readouterr().out


def test_missing_command_exits_with_usage_error():
    with pytest.raises(SystemExit) as exit_info:
        run()
    assert exit_info.value.code == 2


def test_invalid_port_is_a_friendly_error(capsys):
    assert run("serve", "--port", "99999") == 1
    assert "porta" in capsys.readouterr().err


def test_port_from_config_file_is_validated(isolated_cwd, capsys):
    (isolated_cwd / "openops.config.json").write_text(json.dumps({"port": "abc"}), encoding="utf-8")

    assert run("serve") == 1
    assert "porta inválida" in capsys.readouterr().err


def test_broken_config_file_is_a_friendly_error(isolated_cwd, capsys):
    (isolated_cwd / "openops.config.json").write_text("{ isso não é json", encoding="utf-8")

    assert run("version") == 1
    assert "Erro:" in capsys.readouterr().err


def test_init_creates_config_db_and_admin(isolated_cwd, monkeypatch, capsys):
    monkeypatch.setenv("OPENOPS_ADMIN_PASSWORD", "senha-forte-123")

    assert run("init", "--admin", "jose", "--demo") == 0

    assert (isolated_cwd / "openops.config.json").exists()
    assert (isolated_cwd / "openops.db").exists()
    assert (isolated_cwd / "openops.log").exists()
    assert "Administrador 'jose' criado" in capsys.readouterr().out


def test_init_is_idempotent(monkeypatch, capsys):
    monkeypatch.setenv("OPENOPS_ADMIN_PASSWORD", "senha-forte-123")
    run("init", "--admin", "jose", "--demo")
    capsys.readouterr()

    assert run("init", "--admin", "outro", "--demo") == 0
    out = capsys.readouterr().out
    assert "Já existe um administrador" in out and "demonstração ignorada" in out


def test_init_with_weak_password_fails_cleanly(monkeypatch, capsys):
    monkeypatch.setenv("OPENOPS_ADMIN_PASSWORD", "123")

    assert run("init", "--admin", "jose") == 1
    assert "senha" in capsys.readouterr().err.lower()


def test_expiry_lists_demo_batch_as_json(monkeypatch, capsys):
    monkeypatch.setenv("OPENOPS_ADMIN_PASSWORD", "senha-forte-123")
    run("init", "--admin", "jose", "--demo")
    capsys.readouterr()

    assert run("expiry", "--days", "60", "--json") == 0
    rows = json.loads(capsys.readouterr().out)

    assert [r["product_name"] for r in rows] == ["Álcool em gel 500 ml"]


def test_expiry_exit_code_for_scripts(monkeypatch, capsys):
    monkeypatch.setenv("OPENOPS_ADMIN_PASSWORD", "senha-forte-123")
    run("init", "--admin", "jose", "--demo")

    assert run("expiry", "--days", "60", "--fail-on-found") == 1
    assert run("expiry", "--days", "5", "--fail-on-found") == 0


def test_expiry_rejects_nonpositive_days():
    with pytest.raises(SystemExit):
        run("expiry", "--days", "0")


def test_export_writes_csv_with_header(isolated_cwd, monkeypatch):
    monkeypatch.setenv("OPENOPS_ADMIN_PASSWORD", "senha-forte-123")
    run("init", "--admin", "jose", "--demo")

    assert run("export", "products", "-o", "out.csv") == 0

    text = (isolated_cwd / "out.csv").read_text(encoding="utf-8-sig")
    assert text.splitlines()[0] == "id,nome,categoria,preco,estoque,valor_em_estoque"
    assert "Caneca de cerâmica 300 ml" in text


def test_db_flag_overrides_default(isolated_cwd, monkeypatch):
    monkeypatch.setenv("OPENOPS_ADMIN_PASSWORD", "senha-forte-123")

    assert run("--db", "outro.db", "init", "--admin", "jose") == 0
    assert (isolated_cwd / "outro.db").exists() and not (isolated_cwd / "openops.db").exists()


def test_reset_password_lets_user_log_in_again(monkeypatch, capsys):
    monkeypatch.setenv("OPENOPS_ADMIN_PASSWORD", "senha-forte-123")
    run("init", "--admin", "jose")
    monkeypatch.setenv("OPENOPS_NEW_PASSWORD", "outra-senha-456")

    assert run("reset-password", "jose") == 0

    from openops_web import WebApp

    app = WebApp(db_path="openops.db")
    assert app.users.authenticate(username="jose", password="outra-senha-456")
    app.close()


def test_reset_password_for_unknown_user_is_a_clean_error(monkeypatch, capsys):
    monkeypatch.setenv("OPENOPS_ADMIN_PASSWORD", "senha-forte-123")
    run("init", "--admin", "jose")
    monkeypatch.setenv("OPENOPS_NEW_PASSWORD", "outra-senha-456")

    assert run("reset-password", "fantasma") == 1
    assert "não encontrado" in capsys.readouterr().err


def test_cli_survives_a_cp1252_console(isolated_cwd):
    """Regressão (Windows/Git Bash): saída em cp1252 derrubava o `init` por causa de "✓"."""
    import os
    import subprocess

    env = dict(os.environ, PYTHONIOENCODING="cp1252", OPENOPS_ADMIN_PASSWORD="senha-forte-123")
    result = subprocess.run(
        [sys.executable, str(Path(openops.__file__)), "init", "--admin", "jose"],
        capture_output=True, env=env, cwd=isolated_cwd, timeout=60,
    )

    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert "UnicodeEncodeError" not in result.stderr.decode("utf-8", "replace")


def test_config_file_not_in_utf8_is_a_friendly_error(isolated_cwd, capsys):
    """Regressão (Windows): config salvo em ANSI/cp1252 não pode virar traceback."""
    (isolated_cwd / "openops.config.json").write_bytes('{ "nome": "não" }'.encode("cp1252"))

    assert run("version") == 1
    assert "UTF-8" in capsys.readouterr().err
