from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.application.ports.outbox_repository import AbstractOutboxRepository
    from app.domain.repositories.payment_repository import AbstractPaymentRepository


class AbstractUnitOfWork(ABC):
    payment_repo: "AbstractPaymentRepository"
    outbox_repo: "AbstractOutboxRepository"

    async def __aenter__(self) -> "AbstractUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            await self.rollback()
        else:
            await self.commit()

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
