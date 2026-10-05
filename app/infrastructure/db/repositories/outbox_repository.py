from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.outbox_repository import AbstractOutboxRepository, OutboxEvent
from app.infrastructure.db.models.outbox import OutboxModel


class SqlAlchemyOutboxRepository(AbstractOutboxRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, payment_id: UUID, event_type: str, payload: dict) -> None:
        model = OutboxModel(
            id=uuid4(),
            payment_id=payment_id,
            event_type=event_type,
            payload=payload,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(model)
        await self._session.flush()

    async def get_unpublished(self, limit: int = 10) -> list[OutboxEvent]:
        stmt = (
            select(OutboxModel)
            .where(OutboxModel.published_at.is_(None))
            .order_by(OutboxModel.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)  # безопасно при нескольких инстансах
        )
        result = await self._session.execute(stmt)
        return [
            OutboxEvent(id=m.id, event_type=m.event_type, payload=m.payload)
            for m in result.scalars().all()
        ]

    async def mark_published(self, outbox_id: UUID) -> None:
        stmt = (
            update(OutboxModel)
            .where(OutboxModel.id == outbox_id)
            .values(published_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)
