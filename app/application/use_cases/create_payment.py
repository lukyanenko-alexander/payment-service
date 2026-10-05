from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.application.unit_of_work import AbstractUnitOfWork
from app.domain.entities.payment import Payment
from app.domain.enums import Currency, PaymentStatus
from app.domain.value_objects.money import Money


@dataclass
class CreatePaymentCommand:
    amount: Decimal
    currency: Currency
    description: str
    idempotency_key: str
    webhook_url: str
    metadata: dict


@dataclass
class CreatePaymentResult:
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime


class CreatePaymentUseCase:
    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, command: CreatePaymentCommand) -> CreatePaymentResult:
        async with self._uow as uow:
            existing = await uow.payment_repo.get_by_idempotency_key(command.idempotency_key)
            if existing:
                return CreatePaymentResult(
                    payment_id=existing.id,
                    status=existing.status,
                    created_at=existing.created_at,
                )

            Money(amount=command.amount, currency=command.currency)

            payment = Payment(
                amount=command.amount,
                currency=command.currency,
                description=command.description,
                idempotency_key=command.idempotency_key,
                webhook_url=command.webhook_url,
                metadata=command.metadata,
            )

            await uow.payment_repo.save(payment)
            await uow.outbox_repo.save(
                payment_id=payment.id,
                event_type="payment.created",
                payload={"payment_id": str(payment.id)},
            )

        return CreatePaymentResult(
            payment_id=payment.id,
            status=payment.status,
            created_at=payment.created_at,
        )
