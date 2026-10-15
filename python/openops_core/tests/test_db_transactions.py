# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""Transações e thread-safety da camada de banco (correções feitas para o micro-site)."""

from concurrent.futures import ThreadPoolExecutor

import pytest

from openops_core.db import Database, Migration

TABLE = Migration(version=1, name="t", namespace="t", sql="CREATE TABLE t (id INTEGER PRIMARY KEY, v INTEGER NOT NULL);")


@pytest.fixture
def db():
    database = Database(":memory:")
    database.migrate([TABLE])
    return database


def count(db):
    return db.query("SELECT COUNT(*) AS n FROM t")[0]["n"]


def test_transaction_commits_all_on_success(db):
    with db.transaction():
        db.execute("INSERT INTO t (v) VALUES (1)")
        db.execute("INSERT INTO t (v) VALUES (2)")

    assert count(db) == 2


def test_transaction_rolls_back_everything_on_error(db):
    with pytest.raises(RuntimeError):
        with db.transaction():
            db.execute("INSERT INTO t (v) VALUES (1)")
            raise RuntimeError("falhou no meio")

    assert count(db) == 0


def test_nested_transactions_commit_only_at_the_outermost_level(db):
    with pytest.raises(RuntimeError):
        with db.transaction():
            with db.transaction():
                db.execute("INSERT INTO t (v) VALUES (1)")
            raise RuntimeError("erro depois do bloco interno")

    assert count(db) == 0


def test_autocommit_resumes_after_transaction(db):
    with db.transaction():
        db.execute("INSERT INTO t (v) VALUES (1)")
    db.execute("INSERT INTO t (v) VALUES (2)")

    assert count(db) == 2


def test_concurrent_queries_always_get_named_rows(db):
    """Regressão: ``row_factory`` compartilhado fazia threads receberem
    tuplas e quebrarem com TypeError em ``row['coluna']``."""
    db.execute("INSERT INTO t (v) VALUES (7)")

    def work(_):
        return db.query("SELECT v FROM t")[0]["v"]

    with ThreadPoolExecutor(max_workers=16) as pool:
        assert set(pool.map(work, range(400))) == {7}
