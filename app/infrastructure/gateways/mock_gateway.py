import asyncio
import random
from decimal import Decimal
from uuid import UUID

from app.application.ports.payment_gateway import AbstractPaymentGateway, GatewayResult
from app.domain.enums import PaymentStatus


class MockPaymentGateway(AbstractPaymentGateway):
    async def process(self, payment_id: UUID, amount: Decimal, currency: str) -> GatewayResult:
        await asyncio.sleep(random.uniform(2, 5))

        if random.random() < 0.9:
            return GatewayResult(status=PaymentStatus.SUCCEEDED)

        return GatewayResult(
            status=PaymentStatus.FAILED,
            error_message="Payment declined by gateway",
        )
