from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass
class OutboxEvent:
    id: UUID
    event_type: str
    payload: dict


class AbstractOutboxRepository(ABC):
    @abstractmethod
    async def save(self, payment_id: UUID, event_type: str, payload: dict) -> None: ...

    @abstractmethod
    async def get_unpublished(self, limit: int = 10) -> list[OutboxEvent]: ...

    @abstractmethod
    async def mark_published(self, outbox_id: UUID) -> None: ...
