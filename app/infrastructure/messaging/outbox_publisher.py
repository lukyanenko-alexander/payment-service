import asyncio
import logging

from app.application.ports.message_broker import AbstractMessageBroker
from app.config import settings
from app.infrastructure.db.database import async_session_factory
from app.infrastructure.db.repositories.outbox_repository import SqlAlchemyOutboxRepository

logger = logging.getLogger(__name__)


async def run_outbox_publisher(broker: AbstractMessageBroker) -> None:
    """
    Периодически читает неопубликованные события из outbox и отправляет их в RabbitMQ.
    SELECT FOR UPDATE SKIP LOCKED гарантирует безопасность при нескольких инстансах API.
    Запись помечается опубликованной только после успешной отправки в брокер.
    """
    while True:
        try:
            async with async_session_factory.begin() as session:
                repo = SqlAlchemyOutboxRepository(session)
                events = await repo.get_unpublished(limit=10)

                for event in events:
                    await broker.publish(event.payload)
                    await repo.mark_published(event.id)

        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Outbox publisher iteration failed")

        await asyncio.sleep(settings.OUTBOX_POLL_INTERVAL)
