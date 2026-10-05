from faststream.rabbit import RabbitBroker as FastStreamBroker
from faststream.rabbit import RabbitExchange, ExchangeType

from app.application.ports.message_broker import AbstractMessageBroker

_PAYMENTS_EXCHANGE = RabbitExchange("payments", type=ExchangeType.DIRECT, durable=True)


class RabbitMQBroker(AbstractMessageBroker):
    def __init__(self, broker: FastStreamBroker) -> None:
        self._broker = broker

    async def publish(self, payload: dict) -> None:
        await self._broker.publish(
            payload,
            exchange=_PAYMENTS_EXCHANGE,
            routing_key="payments.new",
        )
