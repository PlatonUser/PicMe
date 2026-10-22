from abc import ABC, abstractmethod

from app.domain.round import Round


class RoundRepository(ABC):
    @abstractmethod
    def add(self, round_: Round) -> None:
        raise NotImplementedError

    @abstractmethod
    def save(self, round_: Round) -> None:
        raise NotImplementedError

    @abstractmethod
    def for_game(self, game_code: str) -> list[Round]:
        raise NotImplementedError

    @abstractmethod
    def current(self, game_code: str) -> Round | None:
        raise NotImplementedError
