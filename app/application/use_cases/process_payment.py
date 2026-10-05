from uuid import UUID

from app.application.ports.payment_gateway import AbstractPaymentGateway
from app.application.ports.webhook_sender import AbstractWebhookSender
from app.application.unit_of_work import AbstractUnitOfWork
from app.domain.enums import PaymentStatus


class ProcessPaymentUseCase:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        gateway: AbstractPaymentGateway,
        webhook_sender: AbstractWebhookSender,
    ) -> None:
        self._uow = uow
        self._gateway = gateway
        self._webhook_sender = webhook_sender

    async def execute(self, payment_id: UUID) -> None:
        async with self._uow as uow:
            payment = await uow.payment_repo.get_by_id(payment_id)
            if not payment:
                raise ValueError(f"Payment {payment_id} not found")

            if payment.status != PaymentStatus.PENDING:
                return

            result = await self._gateway.process(
                payment_id=payment.id,
                amount=payment.amount,
                currency=payment.currency.value,
            )

            if result.status == PaymentStatus.SUCCEEDED:
                payment.mark_succeeded()
            else:
                payment.mark_failed()

            await uow.payment_repo.update(payment)

        # Webhook отправляется после коммита транзакции, но до ack сообщения в consumer-е.
        # Это значит сообщение остаётся unacknowledged во время retry-задержек webhook-а,
        # что снижает пропускную способность при низком prefetch_count.
        # В продакшне: вынести в отдельную задачу после ack или реализовать webhook outbox.
        await self._webhook_sender.send(
            webhook_url=payment.webhook_url,
            payment_id=payment.id,
            status=payment.status,
        )
