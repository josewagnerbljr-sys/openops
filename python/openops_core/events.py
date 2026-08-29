"""
openops_core.events
====================

Event bus síncrono, thread-safe, em processo. É a base sobre a qual os
"gatilhos" e o "histórico de execução" descritos na camada Operations do
OpenOps serão construídos. Um backend distribuído (Go, worker via fila)
poderá substituir este backend "memory" no futuro sem mudar a interface
pública (``EventBus.subscribe`` / ``EventBus.publish``).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, DefaultDict
from collections import defaultdict

EventHandler = Callable[["Event"], None]


@dataclass(frozen=True)
class Event:
    """Um evento publicado no barramento.

    Attributes:
        name: identificador do evento, ex. "sop.completed", "stock.low".
        payload: dados livres associados ao evento.
        occurred_at: timestamp UTC de criação do evento.
    """

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class EventBus:
    """Barramento de eventos em memória, com publicação síncrona.

    Um handler que levanta exceção não interrompe os handlers seguintes:
    o erro é coletado e re-levantado como ``ExceptionGroup``-like ao final
    da publicação, para que um assinante com bug não derrube o sistema
    inteiro — alinhado ao princípio de resiliência do OpenOps.
    """

    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, list[EventHandler]] = defaultdict(list)
        self._lock = threading.RLock()

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        with self._lock:
            self._subscribers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        with self._lock:
            handlers = self._subscribers.get(event_name, [])
            if handler in handlers:
                handlers.remove(handler)

    def publish(self, event_name: str, payload: dict[str, Any] | None = None) -> Event:
        event = Event(name=event_name, payload=payload or {})

        with self._lock:
            handlers = list(self._subscribers.get(event_name, []))

        errors: list[BaseException] = []
        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:  # noqa: BLE001 - isolamento intencional
                errors.append(exc)

        if errors:
            raise EventHandlingError(event, errors)

        return event

    def subscriber_count(self, event_name: str) -> int:
        with self._lock:
            return len(self._subscribers.get(event_name, []))


class EventHandlingError(Exception):
    """Agrega os erros levantados por handlers durante uma publicação."""

    def __init__(self, event: Event, errors: list[BaseException]) -> None:
        self.event = event
        self.errors = errors
        summary = "; ".join(f"{type(e).__name__}: {e}" for e in errors)
        super().__init__(
            f"{len(errors)} handler(s) falharam para o evento '{event.name}': {summary}"
        )
