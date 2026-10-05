from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.domain.enums import PaymentStatus


@dataclass
class GatewayResult:
    status: PaymentStatus
    error_message: str | None = None


class AbstractPaymentGateway(ABC):
    @abstractmethod
    async def process(self, payment_id: UUID, amount: Decimal, currency: str) -> GatewayResult: ...
