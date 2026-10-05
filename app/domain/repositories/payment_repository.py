from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.payment import Payment


class AbstractPaymentRepository(ABC):
    @abstractmethod
    async def save(self, payment: Payment) -> None: ...

    @abstractmethod
    async def get_by_id(self, payment_id: UUID) -> Payment | None: ...

    @abstractmethod
    async def get_by_idempotency_key(self, key: str) -> Payment | None: ...

    @abstractmethod
    async def update(self, payment: Payment) -> None: ...
