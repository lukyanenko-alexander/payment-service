from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.enums import PaymentStatus


class AbstractWebhookSender(ABC):
    @abstractmethod
    async def send(self, webhook_url: str, payment_id: UUID, status: PaymentStatus) -> None: ...
