"""
openops_business.inventory.router
==================================

Rotas REST do módulo de Estoque — registrar movimento exige "operator"+
(afeta o estoque real do produto); consultar exige apenas login.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from openops_api.auth import get_current_user, require_role

from .models import StockMovement
from .service import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"])


class MovementCreate(BaseModel):
    product_id: int
    movement_type: str
    quantity: int
    reason: str = ""


class MovementOut(BaseModel):
    id: int
    product_id: int
    movement_type: str
    quantity: int
    reason: str

    @classmethod
    def from_domain(cls, movement: StockMovement) -> "MovementOut":
        return cls(
            id=movement.id,
            product_id=movement.product_id,
            movement_type=movement.movement_type,
            quantity=movement.quantity,
            reason=movement.reason,
        )


def _service(request: Request) -> InventoryService:
    return request.app.state.inventory_service


@router.post(
    "/movements",
    response_model=MovementOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("operator"))],
)
def create_movement(payload: MovementCreate, request: Request) -> MovementOut:
    movement = _service(request).register_movement(
        product_id=payload.product_id,
        movement_type=payload.movement_type,
        quantity=payload.quantity,
        reason=payload.reason,
    )
    return MovementOut.from_domain(movement)


@router.get("/movements", response_model=list[MovementOut], dependencies=[Depends(get_current_user)])
def list_movements(request: Request, product_id: int | None = None) -> list[MovementOut]:
    movements = _service(request).list_movements(product_id=product_id)
    return [MovementOut.from_domain(m) for m in movements]


@router.get("/products/{product_id}/stock", dependencies=[Depends(get_current_user)])
def get_stock(product_id: int, request: Request) -> dict[str, int]:
    stock = _service(request).current_stock(product_id)
    return {"product_id": product_id, "stock": stock}
