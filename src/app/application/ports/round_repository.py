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

    def delete_for_game(self, game_code: str) -> None:
        if hasattr(self, "rounds"):
            self.rounds = [round_ for round_ in self.rounds
                           if getattr(round_, "game_code", None) != game_code]
