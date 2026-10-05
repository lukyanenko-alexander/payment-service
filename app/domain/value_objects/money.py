from dataclasses import dataclass
from decimal import Decimal

from app.domain.enums import Currency


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("Amount must be positive")
