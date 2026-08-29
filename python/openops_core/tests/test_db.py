import pytest

from openops_core.db import Database, Migration, database
from openops_core.errors import MaintenanceError, ValidationError


def test_migrate_applies_in_order_and_records_history():
    db = Database(":memory:")
    migrations = [
        Migration(1, "create_products", "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT);"),
        Migration(2, "add_price_column", "ALTER TABLE products ADD COLUMN price REAL;"),
    ]

    applied = db.migrate(migrations)

    assert applied == [1, 2]
    assert db.applied_versions() == {1, 2}


def test_migrate_skips_already_applied():
    db = Database(":memory:")
    migration = Migration(1, "create_x", "CREATE TABLE x (id INTEGER PRIMARY KEY);")

    first_run = db.migrate([migration])
    second_run = db.migrate([migration])

    assert first_run == [1]
    assert second_run == []  # já aplicada, não reaplica


def test_migrate_duplicate_versions_raises():
    db = Database(":memory:")
    migrations = [
        Migration(1, "a", "CREATE TABLE a (id INTEGER);"),
        Migration(1, "b", "CREATE TABLE b (id INTEGER);"),
    ]

    with pytest.raises(MaintenanceError):
        db.migrate(migrations)


def test_migrate_invalid_sql_raises_maintenance_error_and_rolls_back():
    db = Database(":memory:")
    migrations = [Migration(1, "quebrado", "ISSO NAO E SQL VALIDO;")]

    with pytest.raises(MaintenanceError):
        db.migrate(migrations)

    # a migration inválida não deve ter ficado registrada como aplicada
    assert db.applied_versions() == set()


def test_execute_and_query_roundtrip():
    db = Database(":memory:")
    db.migrate([Migration(1, "create_products", "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT);")])

    db.execute("INSERT INTO products (name) VALUES (?)", ("Café",))
    rows = db.query("SELECT name FROM products")

    assert [row["name"] for row in rows] == ["Café"]


def test_migration_rejects_non_positive_version():
    with pytest.raises(ValidationError):
        Migration(0, "invalida", "SELECT 1;")


def test_migration_rejects_empty_name():
    with pytest.raises(ValidationError):
        Migration(1, "  ", "SELECT 1;")


def test_database_context_manager_closes_connection():
    with database(":memory:") as db:
        db.migrate([Migration(1, "x", "CREATE TABLE x (id INTEGER PRIMARY KEY);")])
        assert db.applied_versions() == {1}
    # depois do bloco `with`, a conexão interna foi fechada
    assert db._conn is None
