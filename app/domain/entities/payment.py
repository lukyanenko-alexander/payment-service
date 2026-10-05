from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.enums import Currency, PaymentStatus


@dataclass
class Payment:
    amount: Decimal
    currency: Currency
    description: str
    idempotency_key: str
    webhook_url: str
    id: UUID = field(default_factory=uuid4)
    status: PaymentStatus = field(default=PaymentStatus.PENDING)
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: datetime | None = None

    def mark_succeeded(self) -> None:
        self.status = PaymentStatus.SUCCEEDED
        self.processed_at = datetime.now(timezone.utc)

    def mark_failed(self) -> None:
        self.status = PaymentStatus.FAILED
        self.processed_at = datetime.now(timezone.utc)
