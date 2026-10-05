from abc import ABC, abstractmethod


class AbstractMessageBroker(ABC):
    @abstractmethod
    async def publish(self, payload: dict) -> None: ...
