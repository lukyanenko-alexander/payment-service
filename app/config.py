from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/payments"
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"
    API_KEY: str = "super-secret-api-key"
    GATEWAY: str = "mock"
    OUTBOX_POLL_INTERVAL: float = 1.0

    model_config = {"env_file": ".env"}


settings = Settings()
