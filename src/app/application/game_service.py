import secrets
from collections.abc import Callable

from app.application.ports.game_repository import GameRepository
from app.domain.errors import NotFound
from app.domain.game import Game, Player


class GameService:
    def __init__(
        self,
        repository: GameRepository,
        round_state_provider: Callable[[str], dict] | None = None,
    ):
        self.repository = repository
        self.round_state_provider = round_state_provider

    def create_game(self) -> Game:
        game = Game.create()
        game.host_token = secrets.token_urlsafe(32)
        self.repository.add(game)
        return game

    def join_game(self, code: str, name: str) -> Player:
        game = self._get(code)
        player = game.add_player(name, self.repository.next_player_id())
        self.repository.save(game)
        return player

    def state(self, code: str) -> dict:
        game = self._get(code)
        result = {
            "code": game.code,
            "phase": game.phase,
            "players": [{"id": player.id, "name": player.name} for player in game.players],
            "message": None,
            "round": None,
            "photo": None,
            "voting": None,
        }
        if self.round_state_provider:
            result.update(self.round_state_provider(code))
        return result

    def set_phase(self, code: str, phase: str) -> None:
        game = self._get(code)
        game.phase = phase
        self.repository.save(game)

    def _get(self, code: str) -> Game:
        game = self.repository.get(code)
        if game is None:
            raise NotFound("Game not found")
        return game
