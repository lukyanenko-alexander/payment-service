import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from faststream.rabbit import RabbitBroker

from app.config import settings
from app.infrastructure.messaging.outbox_publisher import run_outbox_publisher
from app.infrastructure.messaging.rabbitmq_broker import RabbitMQBroker
from app.presentation.api.v1 import payments

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    broker = RabbitBroker(settings.RABBITMQ_URL)
    await broker.start()

    outbox_task = asyncio.create_task(run_outbox_publisher(RabbitMQBroker(broker)))

    yield

    outbox_task.cancel()
    try:
        await asyncio.wait_for(outbox_task, timeout=5.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass

    await broker.close()


app = FastAPI(
    title="Payment Processing Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(payments.router, prefix="/api/v1")
