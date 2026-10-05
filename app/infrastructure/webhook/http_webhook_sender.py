import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

import httpx

from app.application.ports.webhook_sender import AbstractWebhookSender
from app.domain.enums import PaymentStatus

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3
_TIMEOUT = 10.0


class HttpWebhookSender(AbstractWebhookSender):
    async def send(self, webhook_url: str, payment_id: UUID, status: PaymentStatus) -> None:
        payload = {
            "payment_id": str(payment_id),
            "status": status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            for attempt in range(_MAX_ATTEMPTS):
                try:
                    response = await client.post(webhook_url, json=payload)
                    response.raise_for_status()
                    logger.info("Webhook delivered for payment %s", payment_id)
                    return
                except Exception as exc:
                    delay = 2**attempt
                    if attempt < _MAX_ATTEMPTS - 1:
                        logger.warning(
                            "Webhook attempt %d/%d failed for payment %s: %s. Retrying in %ds",
                            attempt + 1, _MAX_ATTEMPTS, payment_id, exc, delay,
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            "Webhook failed after %d attempts for payment %s: %s",
                            _MAX_ATTEMPTS, payment_id, exc,
                        )
