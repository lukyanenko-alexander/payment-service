# Payment Processing Service

Асинхронный микросервис процессинга платежей на FastAPI + RabbitMQ + PostgreSQL.

## Архитектура

Проект построен по принципам **Clean Architecture**:

```
app/
├── domain/          # Сущности и абстракции (нет внешних зависимостей)
├── application/     # Use cases + порты (зависит только от domain)
├── infrastructure/  # Реализации портов (DB, RabbitMQ, HTTP)
├── presentation/    # FastAPI роутеры и схемы
└── worker/          # FastStream consumer
```

### Ключевые паттерны

- **Outbox pattern** — атомарная запись платежа и события в одной транзакции, публикация в RabbitMQ через фоновый поллинг с `SELECT FOR UPDATE SKIP LOCKED`
- **Strategy** — `AbstractPaymentGateway` позволяет подключать любой платёжный шлюз через `GATEWAY=<name>` в `.env`
- **Unit of Work** — `SqlAlchemyUnitOfWork` управляет транзакцией и жизнью сессии
- **Idempotency key** — уникальный индекс на `payments.idempotency_key` + проверка в use case

### RabbitMQ топология

```
[API outbox publisher]
        │
        ▼
Exchange: payments (direct)
        │ routing_key: payments.new
        ▼
Queue: payments.new ──────────────────────────────────────────────────────┐
        │                                                                  │
        ▼                                                                  │
   [Consumer]                                                              │
        ├── success → ack                                                  │
        │                                                                  │
        ├── failure, attempt < 3                                           │
        │       │                                                          │
        │       ▼                                                          │
        │  Exchange: payments.delayed (x-delayed-message)                  │
        │       │  x-delay: 1000ms / 2000ms                               │
        │       └──────────────────────────────────────────────────────────┘
        │
        └── failure, attempt = 3 → nack(requeue=False)
                │
                ▼
        Exchange: payments.dlx (direct)
                │ routing_key: payments.dead
                ▼
        Queue: payments.dead (DLQ)
```

**Retry логика consumer**: 3 попытки с экспоненциальной задержкой (1s → 2s → DLQ). Задержка реализована через плагин `rabbitmq_delayed_message_exchange` — сообщение хранится в exchange N мс, consumer не блокируется.

## Запуск

### Предварительные требования

- Docker и Docker Compose

### Быстрый старт

```bash
# 1. Скопировать конфиг
cp .env.example .env

# 2. Запустить все сервисы
docker compose up --build

# 3. API доступен на http://localhost:8000
# 4. RabbitMQ Management: http://localhost:15672 (guest/guest)
# 5. Swagger UI: http://localhost:8000/docs
```

## API

Все эндпоинты требуют заголовок `X-API-Key`.

### Создать платёж

```bash
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Content-Type: application/json" \
  -H "X-API-Key: super-secret-api-key" \
  -H "Idempotency-Key: unique-key-123" \
  -d '{
    "amount": "100.00",
    "currency": "RUB",
    "description": "Оплата заказа #42",
    "metadata": {"order_id": "42"},
    "webhook_url": "https://webhook.site/your-unique-url"
  }'
```

Ответ `202 Accepted`:
```json
{
  "payment_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2026-09-12T10:00:00Z"
}
```

### Получить статус платежа

```bash
curl http://localhost:8000/api/v1/payments/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: super-secret-api-key"
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | URL PostgreSQL |
| `RABBITMQ_URL` | `amqp://guest:guest@rabbitmq:5672/` | URL RabbitMQ |
| `API_KEY` | `super-secret-api-key` | Статический API ключ |
| `GATEWAY` | `mock` | Платёжный шлюз (`mock` или будущие реализации) |
| `OUTBOX_POLL_INTERVAL` | `1.0` | Интервал поллинга outbox (секунды) |

## Поток обработки платежа

```
POST /api/v1/payments
  → CreatePaymentUseCase
    → [DB transaction] INSERT payments + INSERT outbox
    → 202 Accepted

[Background] OutboxPublisher (каждые 1s)
  → SELECT outbox WHERE published_at IS NULL FOR UPDATE SKIP LOCKED
  → publish → RabbitMQ payments.new
  → UPDATE outbox SET published_at = now()

[Consumer] handle_payment
  → ProcessPaymentUseCase
    → MockPaymentGateway.process() (2-5s, 90%/10%)
    → UPDATE payments SET status = succeeded/failed
  → HttpWebhookSender.send() (3 попытки, backoff 1s/2s/4s)
  → ack / retry / DLQ
```
