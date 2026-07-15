"""
Bus de eventos en memoria (proceso).

Es un singleton simple que permite desacoplar publicadores y suscriptores.
Los adaptadores en infraestructura pueden reemplazar este bus por una
implementacion distribuida (Redis, RabbitMQ, etc.) si fuera necesario.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Callable, Dict, List, Type

logger = logging.getLogger(__name__)


class InMemoryEventBus:
    """Bus de eventos en memoria, sincrono."""

    def __init__(self) -> None:
        self._handlers: Dict[Type, List[Callable]] = defaultdict(list)

    def subscribe(self, event_type: Type, handler: Callable) -> None:
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: Type, handler: Callable) -> None:
        if handler in self._handlers.get(event_type, []):
            self._handlers[event_type].remove(handler)

    def publish(self, event) -> None:
        handlers = list(self._handlers.get(type(event), []))
        for h in handlers:
            try:
                h(event)
            except Exception:
                logger.exception(
                    "Error manejando evento %s en handler %s",
                    type(event).__name__, h,
                )

    def clear(self) -> None:
        self._handlers.clear()


# Singleton global. Tests pueden reemplazar `event_bus` en su setup.
event_bus = InMemoryEventBus()