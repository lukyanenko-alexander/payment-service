from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.application.use_cases.create_payment import CreatePaymentCommand, CreatePaymentUseCase
from app.application.use_cases.get_payment import GetPaymentUseCase
from app.presentation.deps import (
    get_create_payment_use_case,
    get_payment_use_case,
    verify_api_key,
)
from app.presentation.schemas.payment import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    PaymentDetailResponse,
)

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post(
    "/payments",
    response_model=CreatePaymentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Создать платёж",
)
async def create_payment(
    body: CreatePaymentRequest,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    use_case: CreatePaymentUseCase = Depends(get_create_payment_use_case),
) -> CreatePaymentResponse:
    result = await use_case.execute(
        CreatePaymentCommand(
            amount=body.amount,
            currency=body.currency,
            description=body.description,
            idempotency_key=idempotency_key,
            webhook_url=str(body.webhook_url),
            metadata=body.metadata,
        )
    )
    return CreatePaymentResponse(
        payment_id=result.payment_id,
        status=result.status,
        created_at=result.created_at,
    )


@router.get(
    "/payments/{payment_id}",
    response_model=PaymentDetailResponse,
    summary="Получить платёж по ID",
)
async def get_payment(
    payment_id: UUID,
    use_case: GetPaymentUseCase = Depends(get_payment_use_case),
) -> PaymentDetailResponse:
    payment = await use_case.execute(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found",
        )
    return PaymentDetailResponse(
        id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        metadata=payment.metadata,
        status=payment.status,
        idempotency_key=payment.idempotency_key,
        webhook_url=payment.webhook_url,
        created_at=payment.created_at,
        processed_at=payment.processed_at,
    )
