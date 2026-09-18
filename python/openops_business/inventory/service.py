"""
openops_business.inventory.service
===================================

Fachada de negócio do módulo de Estoque. Duas coisas o diferenciam dos
módulos anteriores (Produtos, Clientes):

1. **Depende de outro módulo de negócio** (`ProductService`) para ler e
   atualizar o estoque do produto afetado — a movimentação e a
   atualização do produto acontecem como parte da mesma operação.
2. **Publica eventos** (`stock.changed`, `stock.low`) no `EventBus` do
   core, para que outros módulos (Analytics, Maintenance, um plugin de
   notificação) reajam sem que o Inventory precise conhecê-los.
"""

from __future__ import annotations

from datetime import date, timedelta

from openops_core.db import Database
from openops_core.events import EventBus
from openops_core.registry import ModuleInfo, default_registry

from openops_business.products.service import ProductService

from .models import StockMovement, apply_movement
from .repository import StockMovementRepository, INVENTORY_MIGRATIONS

MODULE_INFO = ModuleInfo(
    name="inventory",
    version="0.2.0",
    category="business",
    description="Movimentação de estoque do Business OS, com lote/validade",
)

#: Abaixo deste nível, um evento "stock.low" é publicado. Valor fixo por
#: enquanto — vira configurável por produto/categoria numa fase futura.
LOW_STOCK_THRESHOLD = 5

#: Quantos dias de antecedência contam como "vencendo em breve" para o
#: evento `stock.expiring_soon`. Pensado para ser configurável por
#: categoria/vertical numa fase futura (farmácia tende a querer uma
#: janela maior que hortifruti, por exemplo).
DEFAULT_EXPIRY_ALERT_DAYS = 30


class InventoryService:
    def __init__(
        self,
        db: Database,
        product_service: ProductService,
        *,
        event_bus: EventBus | None = None,
    ) -> None:
        self._db = db
        self._db.migrate(INVENTORY_MIGRATIONS)
        self._repository = StockMovementRepository(db)
        self._products = product_service
        self._events = event_bus if event_bus is not None else EventBus()

    @property
    def events(self) -> EventBus:
        """Expõe o barramento para quem quiser assinar `stock.changed` /
        `stock.low` (ex.: testes, ou um módulo de notificação futuro).
        """
        return self._events

    def register_movement(
        self,
        *,
        product_id: int,
        movement_type: str,
        quantity: int,
        reason: str = "",
        batch_number: str = "",
        expiry_date: date | None = None,
    ) -> StockMovement:
        product = self._products.get_product(product_id)  # NotFoundError se não existir

        new_stock = apply_movement(product.stock, movement_type, quantity)

        movement = StockMovement(
            product_id=product_id,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
            batch_number=batch_number,
            expiry_date=expiry_date,
        )
        saved = self._repository.create(movement)

        self._products.update_product(product_id, stock=new_stock)

        self._events.publish(
            "stock.changed",
            {"product_id": product_id, "movement_type": movement_type, "new_stock": new_stock},
        )
        if new_stock <= LOW_STOCK_THRESHOLD:
            self._events.publish("stock.low", {"product_id": product_id, "stock": new_stock})

        return saved

    def list_movements(self, *, product_id: int | None = None) -> list[StockMovement]:
        return self._repository.list(product_id=product_id)

    def current_stock(self, product_id: int) -> int:
        return self._products.get_product(product_id).stock

    def check_expiring_batches(
        self, *, within_days: int = DEFAULT_EXPIRY_ALERT_DAYS, reference_date: date | None = None
    ) -> list[StockMovement]:
        """Verifica lotes com validade dentro da janela informada e publica
        um evento ``stock.expiring_soon`` por lote encontrado.

        Não é chamado automaticamente a cada movimento — validade se
        aproxima com a passagem do tempo, não com uma transação de
        estoque. Este método é feito para ser acionado por um agendador
        externo (ex.: uma AWS Lambda com EventBridge Schedule rodando uma
        vez por dia), o que o mantém desacoplado de qualquer motor de
        agendamento específico.

        Retorna a lista de lotes encontrados (ordenados por validade
        ascendente — FEFO), além de publicar os eventos correspondentes.
        """
        today = reference_date if reference_date is not None else date.today()
        deadline = today + timedelta(days=within_days)

        expiring = self._repository.list_expiring_batches(on_or_before=deadline)

        for movement in expiring:
            self._events.publish(
                "stock.expiring_soon",
                {
                    "product_id": movement.product_id,
                    "batch_number": movement.batch_number,
                    "expiry_date": movement.expiry_date.isoformat(),
                    "quantity": movement.quantity,
                    "days_remaining": (movement.expiry_date - today).days,
                },
            )

        return expiring


def register(registry=None) -> None:
    (registry if registry is not None else default_registry).register(MODULE_INFO)
