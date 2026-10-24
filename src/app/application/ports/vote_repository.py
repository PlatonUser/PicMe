from abc import ABC, abstractmethod

from app.domain.vote import Vote


class VoteRepository(ABC):
    @abstractmethod
    def get(self, photo_id: int) -> Vote | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, vote: Vote) -> None:
        raise NotImplementedError
