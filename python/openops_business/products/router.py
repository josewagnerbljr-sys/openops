"""
openops_business.products.router
=================================

Rotas REST do módulo de Produtos. Leitura exige apenas estar
autenticado; criação/edição/remoção exigem papel "operator" ou
superior (ver `openops_api.auth`).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from openops_api.auth import get_current_user, require_role

from .models import Product
from .service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


class ProductCreate(BaseModel):
    name: str
    price: float
    stock: int = 0
    category: str = ""


class ProductUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    stock: int | None = None
    category: str | None = None


class ProductOut(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    category: str

    @classmethod
    def from_domain(cls, product: Product) -> "ProductOut":
        return cls(
            id=product.id,
            name=product.name,
            price=product.price,
            stock=product.stock,
            category=product.category,
        )


def _service(request: Request) -> ProductService:
    return request.app.state.product_service


@router.post(
    "",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("operator"))],
)
def create_product(payload: ProductCreate, request: Request) -> ProductOut:
    product = _service(request).create_product(
        name=payload.name, price=payload.price, stock=payload.stock, category=payload.category
    )
    return ProductOut.from_domain(product)


@router.get("", response_model=list[ProductOut], dependencies=[Depends(get_current_user)])
def list_products(request: Request, category: str | None = None) -> list[ProductOut]:
    products = _service(request).list_products(category=category)
    return [ProductOut.from_domain(p) for p in products]


@router.get("/{product_id}", response_model=ProductOut, dependencies=[Depends(get_current_user)])
def get_product(product_id: int, request: Request) -> ProductOut:
    product = _service(request).get_product(product_id)
    return ProductOut.from_domain(product)


@router.put(
    "/{product_id}",
    response_model=ProductOut,
    dependencies=[Depends(require_role("operator"))],
)
def update_product(product_id: int, payload: ProductUpdate, request: Request) -> ProductOut:
    product = _service(request).update_product(
        product_id,
        name=payload.name,
        price=payload.price,
        stock=payload.stock,
        category=payload.category,
    )
    return ProductOut.from_domain(product)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("operator"))],
)
def delete_product(product_id: int, request: Request) -> None:
    _service(request).delete_product(product_id)
