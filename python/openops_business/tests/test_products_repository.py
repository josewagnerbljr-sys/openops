import pytest

from openops_core.db import Database
from openops_core.errors import ConflictError, NotFoundError
from openops_business.products.models import Product
from openops_business.products.repository import ProductRepository, PRODUCTS_MIGRATIONS


@pytest.fixture
def repo() -> ProductRepository:
    db = Database(":memory:")
    db.migrate(PRODUCTS_MIGRATIONS)
    return ProductRepository(db)


def test_create_assigns_id_and_timestamps(repo):
    created = repo.create(Product(name="Bolo de Cenoura", price=15.0, category="doces"))

    assert created.id is not None
    assert created.created_at is not None
    assert created.updated_at is not None


def test_create_duplicate_name_raises_conflict(repo):
    repo.create(Product(name="Pão Francês", price=1.0))

    with pytest.raises(ConflictError):
        repo.create(Product(name="Pão Francês", price=1.5))


def test_get_unknown_id_raises_not_found(repo):
    with pytest.raises(NotFoundError):
        repo.get(999)


def test_list_returns_all_ordered_by_name(repo):
    repo.create(Product(name="Zebra", price=1.0))
    repo.create(Product(name="Abacaxi", price=1.0))

    products = repo.list()

    assert [p.name for p in products] == ["Abacaxi", "Zebra"]


def test_list_filters_by_category(repo):
    repo.create(Product(name="Café", price=8.0, category="bebidas"))
    repo.create(Product(name="Guardanapo", price=2.0, category="descartáveis"))

    bebidas = repo.list(category="bebidas")

    assert [p.name for p in bebidas] == ["Café"]


def test_update_changes_fields(repo):
    created = repo.create(Product(name="Suco", price=6.0, stock=5))

    updated = repo.update(created.id, created.with_updates(price=7.5, stock=10))

    assert updated.price == 7.5
    assert updated.stock == 10
    assert updated.id == created.id


def test_update_unknown_id_raises_not_found(repo):
    fake = Product(name="X", price=1.0)

    with pytest.raises(NotFoundError):
        repo.update(999, fake)


def test_update_to_duplicate_name_raises_conflict(repo):
    repo.create(Product(name="A", price=1.0))
    b = repo.create(Product(name="B", price=1.0))

    with pytest.raises(ConflictError):
        repo.update(b.id, b.with_updates(name="A"))


def test_delete_removes_product(repo):
    created = repo.create(Product(name="Descartável", price=1.0))

    repo.delete(created.id)

    with pytest.raises(NotFoundError):
        repo.get(created.id)


def test_delete_unknown_id_raises_not_found(repo):
    with pytest.raises(NotFoundError):
        repo.delete(999)
