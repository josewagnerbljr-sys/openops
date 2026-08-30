import pytest

from openops_core.db import Database
from openops_core.errors import ConflictError, NotFoundError
from openops_business.customers.models import Customer
from openops_business.customers.repository import CustomerRepository, CUSTOMERS_MIGRATIONS


@pytest.fixture
def repo() -> CustomerRepository:
    db = Database(":memory:")
    db.migrate(CUSTOMERS_MIGRATIONS)
    return CustomerRepository(db)


def test_create_assigns_id_and_timestamps(repo):
    created = repo.create(Customer(name="João Souza", email="joao@exemplo.com"))

    assert created.id is not None
    assert created.created_at is not None


def test_multiple_customers_without_email_are_allowed(repo):
    a = repo.create(Customer(name="Cliente Balcão A"))
    b = repo.create(Customer(name="Cliente Balcão B"))

    assert a.id != b.id  # nenhum conflito, mesmo os dois sem e-mail


def test_duplicate_email_raises_conflict(repo):
    repo.create(Customer(name="Pedro", email="pedro@exemplo.com"))

    with pytest.raises(ConflictError):
        repo.create(Customer(name="Pedro Outro", email="pedro@exemplo.com"))


def test_get_unknown_id_raises_not_found(repo):
    with pytest.raises(NotFoundError):
        repo.get(999)


def test_list_search_filters_by_name_substring(repo):
    repo.create(Customer(name="Ana Paula"))
    repo.create(Customer(name="Ana Beatriz"))
    repo.create(Customer(name="Carlos"))

    result = repo.list(search="Ana")

    assert {c.name for c in result} == {"Ana Paula", "Ana Beatriz"}


def test_update_changes_fields(repo):
    created = repo.create(Customer(name="Lucas", phone="111"))

    updated = repo.update(created.id, created.with_updates(phone="222"))

    assert updated.phone == "222"


def test_delete_removes_customer(repo):
    created = repo.create(Customer(name="Temporário"))

    repo.delete(created.id)

    with pytest.raises(NotFoundError):
        repo.get(created.id)
