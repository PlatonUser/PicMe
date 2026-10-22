from abc import ABC, abstractmethod

from app.domain.game import Game


class GameRepository(ABC):
    @abstractmethod
    def add(self, game: Game) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, code: str) -> Game | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, game: Game) -> None:
        raise NotImplementedError

    @abstractmethod
    def next_player_id(self) -> int:
        raise NotImplementedError
