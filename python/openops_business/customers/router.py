"""
openops_business.customers.router
==================================

Rotas REST do módulo de Clientes — mesma política de acesso do módulo
de Produtos: leitura exige login, escrita exige papel "operator"+.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from openops_api.auth import get_current_user, require_role

from .models import Customer
from .service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


class CustomerCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    document: str | None = None


class CustomerUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    document: str | None = None


class CustomerOut(BaseModel):
    id: int
    name: str
    email: str | None
    phone: str | None
    document: str | None

    @classmethod
    def from_domain(cls, customer: Customer) -> "CustomerOut":
        return cls(
            id=customer.id,
            name=customer.name,
            email=customer.email,
            phone=customer.phone,
            document=customer.document,
        )


def _service(request: Request) -> CustomerService:
    return request.app.state.customer_service


@router.post(
    "",
    response_model=CustomerOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("operator"))],
)
def create_customer(payload: CustomerCreate, request: Request) -> CustomerOut:
    customer = _service(request).create_customer(
        name=payload.name, email=payload.email, phone=payload.phone, document=payload.document
    )
    return CustomerOut.from_domain(customer)


@router.get("", response_model=list[CustomerOut], dependencies=[Depends(get_current_user)])
def list_customers(request: Request, search: str | None = None) -> list[CustomerOut]:
    customers = _service(request).list_customers(search=search)
    return [CustomerOut.from_domain(c) for c in customers]


@router.get("/{customer_id}", response_model=CustomerOut, dependencies=[Depends(get_current_user)])
def get_customer(customer_id: int, request: Request) -> CustomerOut:
    customer = _service(request).get_customer(customer_id)
    return CustomerOut.from_domain(customer)


@router.put(
    "/{customer_id}",
    response_model=CustomerOut,
    dependencies=[Depends(require_role("operator"))],
)
def update_customer(customer_id: int, payload: CustomerUpdate, request: Request) -> CustomerOut:
    customer = _service(request).update_customer(
        customer_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        document=payload.document,
    )
    return CustomerOut.from_domain(customer)


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("operator"))],
)
def delete_customer(customer_id: int, request: Request) -> None:
    _service(request).delete_customer(customer_id)
