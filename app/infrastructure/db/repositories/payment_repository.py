from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.payment import Payment
from app.domain.enums import Currency, PaymentStatus
from app.domain.repositories.payment_repository import AbstractPaymentRepository
from app.infrastructure.db.models.payment import PaymentModel


class SqlAlchemyPaymentRepository(AbstractPaymentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: PaymentModel) -> Payment:
        return Payment(
            id=model.id,
            amount=model.amount,
            currency=Currency(model.currency),
            description=model.description,
            idempotency_key=model.idempotency_key,
            webhook_url=model.webhook_url,
            status=PaymentStatus(model.status),
            metadata=model.payment_metadata or {},
            created_at=model.created_at,
            processed_at=model.processed_at,
        )

    async def save(self, payment: Payment) -> None:
        model = PaymentModel(
            id=payment.id,
            amount=payment.amount,
            currency=payment.currency.value,
            description=payment.description,
            idempotency_key=payment.idempotency_key,
            webhook_url=payment.webhook_url,
            status=payment.status.value,
            payment_metadata=payment.metadata,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
        )
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        model = await self._session.get(PaymentModel, payment_id)
        return self._to_entity(model) if model else None

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        stmt = select(PaymentModel).where(PaymentModel.idempotency_key == key)
        model = await self._session.scalar(stmt)
        return self._to_entity(model) if model else None

    async def update(self, payment: Payment) -> None:
        stmt = (
            update(PaymentModel)
            .where(PaymentModel.id == payment.id)
            .values(status=payment.status.value, processed_at=payment.processed_at)
        )
        await self._session.execute(stmt)
