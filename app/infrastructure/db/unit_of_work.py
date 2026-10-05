from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.unit_of_work import AbstractUnitOfWork
from app.infrastructure.db.repositories.outbox_repository import SqlAlchemyOutboxRepository
from app.infrastructure.db.repositories.payment_repository import SqlAlchemyPaymentRepository


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self._session: AsyncSession = self._session_factory()
        self.payment_repo = SqlAlchemyPaymentRepository(self._session)
        self.outbox_repo = SqlAlchemyOutboxRepository(self._session)
        return await super().__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await super().__aexit__(exc_type, exc_val, exc_tb)
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
