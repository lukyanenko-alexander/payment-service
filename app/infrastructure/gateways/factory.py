from app.application.ports.payment_gateway import AbstractPaymentGateway
from app.config import settings
from app.infrastructure.gateways.mock_gateway import MockPaymentGateway


def get_gateway() -> AbstractPaymentGateway:
    match settings.GATEWAY:
        case "mock":
            return MockPaymentGateway()
        case _:
            raise ValueError(f"Unknown gateway: {settings.GATEWAY!r}")
