from fastapi import Depends, Header, HTTPException, status

from app.application.unit_of_work import AbstractUnitOfWork
from app.application.use_cases.create_payment import CreatePaymentUseCase
from app.application.use_cases.get_payment import GetPaymentUseCase
from app.config import settings
from app.infrastructure.db.database import async_session_factory
from app.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork


def get_uow() -> AbstractUnitOfWork:
    return SqlAlchemyUnitOfWork(async_session_factory)


def get_create_payment_use_case(
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> CreatePaymentUseCase:
    return CreatePaymentUseCase(uow)


def get_payment_use_case(
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> GetPaymentUseCase:
    return GetPaymentUseCase(uow)


async def verify_api_key(x_api_key: str = Header()) -> None:
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
