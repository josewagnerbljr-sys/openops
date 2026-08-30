import pytest

from openops_core.db import Database
from openops_core.errors import NotFoundError
from openops_business.products.service import ProductService
from openops_business.inventory.models import StockMovement
from openops_business.inventory.repository import StockMovementRepository, INVENTORY_MIGRATIONS


@pytest.fixture
def repo_and_products():
    db = Database(":memory:")
    products = ProductService(db)  # cria a tabela products de verdade
    db.migrate(INVENTORY_MIGRATIONS)
    return StockMovementRepository(db), products


@pytest.fixture
def repo(repo_and_products) -> StockMovementRepository:
    return repo_and_products[0]


def test_create_assigns_id_and_timestamp(repo_and_products):
    repo, products = repo_and_products
    product = products.create_product(name="Caneca", price=10.0)

    created = repo.create(StockMovement(product_id=product.id, movement_type="in", quantity=10))

    assert created.id is not None
    assert created.created_at is not None


def test_get_unknown_id_raises_not_found(repo):
    with pytest.raises(NotFoundError):
        repo.get(999)


def test_list_filters_by_product(repo_and_products):
    repo, products = repo_and_products
    product_a = products.create_product(name="Produto A", price=1.0)
    product_b = products.create_product(name="Produto B", price=1.0)
    repo.create(StockMovement(product_id=product_a.id, movement_type="in", quantity=5))
    repo.create(StockMovement(product_id=product_b.id, movement_type="in", quantity=3))

    result = repo.list(product_id=product_a.id)

    assert len(result) == 1
    assert result[0].product_id == product_a.id


def test_list_without_filter_returns_all_newest_first(repo_and_products):
    repo, products = repo_and_products
    product = products.create_product(name="Produto", price=1.0)
    first = repo.create(StockMovement(product_id=product.id, movement_type="in", quantity=1, reason="primeiro"))
    second = repo.create(StockMovement(product_id=product.id, movement_type="in", quantity=2, reason="segundo"))

    result = repo.list()

    assert result[0].id == second.id  # mais recente primeiro
    assert result[1].id == first.id
