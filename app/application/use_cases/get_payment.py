from uuid import UUID

from app.application.unit_of_work import AbstractUnitOfWork
from app.domain.entities.payment import Payment


class GetPaymentUseCase:
    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, payment_id: UUID) -> Payment | None:
        async with self._uow as uow:
            return await uow.payment_repo.get_by_id(payment_id)
