import asyncio
import logging
from uuid import UUID

import aio_pika
from faststream import FastStream
from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange, RabbitMessage, RabbitQueue

from app.application.use_cases.process_payment import ProcessPaymentUseCase
from app.config import settings
from app.infrastructure.db.database import async_session_factory
from app.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.gateways.factory import get_gateway
from app.infrastructure.webhook.http_webhook_sender import HttpWebhookSender

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
_DELAYED_EXCHANGE = "payments.delayed"

broker = RabbitBroker(settings.RABBITMQ_URL)
app = FastStream(broker)

PAYMENTS_EXCHANGE = RabbitExchange("payments", type=ExchangeType.DIRECT, durable=True)
PAYMENTS_QUEUE = RabbitQueue(
    "payments.new",
    durable=True,
    arguments={
        "x-dead-letter-exchange": "payments.dlx",
        "x-dead-letter-routing-key": "payments.dead",
    },
)


async def _setup_infrastructure() -> None:
    """
    Объявляем всю RabbitMQ инфраструктуру до старта FastStream:
    - DLX + DLQ для сообщений, исчерпавших попытки
    - Delayed exchange (плагин rabbitmq_delayed_message_exchange):
      сообщение хранится в exchange N мс, затем роутится в payments.new.
      Consumer свободен сразу — задержка на стороне брокера.
    """
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()

        # Main exchange + queue (объявляем явно чтобы сделать binding с delayed)
        payments_ex = await channel.declare_exchange(
            "payments", aio_pika.ExchangeType.DIRECT, durable=True
        )
        payments_queue = await channel.declare_queue(
            "payments.new",
            durable=True,
            arguments={
                "x-dead-letter-exchange": "payments.dlx",
                "x-dead-letter-routing-key": "payments.dead",
            },
        )
        await payments_queue.bind(payments_ex, routing_key="payments.new")

        dlx = await channel.declare_exchange(
            "payments.dlx", aio_pika.ExchangeType.DIRECT, durable=True
        )
        dlq = await channel.declare_queue("payments.dead", durable=True)
        await dlq.bind(dlx, routing_key="payments.dead")

        # Delayed exchange — тип "x-delayed-message" из плагина.
        # x-delayed-type: direct означает что после задержки сообщение
        # роутится как обычный direct exchange.
        delayed_ex = await channel.declare_exchange(
            _DELAYED_EXCHANGE,
            "x-delayed-message",
            durable=True,
            arguments={"x-delayed-type": "direct"},
        )
        await payments_queue.bind(delayed_ex, routing_key="payments.new")

        logger.info("RabbitMQ infrastructure declared")


def _make_use_case() -> ProcessPaymentUseCase:
    return ProcessPaymentUseCase(
        uow=SqlAlchemyUnitOfWork(async_session_factory),
        gateway=get_gateway(),
        webhook_sender=HttpWebhookSender(),
    )


@broker.subscriber(PAYMENTS_QUEUE, PAYMENTS_EXCHANGE, no_ack=True)
async def handle_payment(payload: dict, msg: RabbitMessage) -> None:
    retry_count = int(msg.headers.get("x-retry-count", 0))
    payment_id = UUID(payload["payment_id"])

    try:
        await _make_use_case().execute(payment_id)
        await msg.ack()
        logger.info("Payment %s processed successfully", payment_id)

    except Exception as exc:
        logger.error(
            "Payment %s failed (attempt %d/%d): %s",
            payment_id, retry_count + 1, MAX_RETRIES, exc,
        )

        if retry_count < MAX_RETRIES - 1:
            delay_ms = 2 ** retry_count * 1000
            logger.info("Scheduling retry for payment %s in %dms", payment_id, delay_ms)
            await broker.publish(
                payload,
                exchange=_DELAYED_EXCHANGE,
                routing_key="payments.new",
                headers={
                    "x-retry-count": retry_count + 1,
                    "x-delay": delay_ms,
                },
            )
            await msg.ack()
        else:
            await msg.nack(requeue=False)
            logger.error("Payment %s moved to DLQ after %d attempts", payment_id, MAX_RETRIES)


async def main() -> None:
    await _setup_infrastructure()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
