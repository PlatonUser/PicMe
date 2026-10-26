import secrets
from dataclasses import dataclass, field

from app.domain.errors import Conflict, InvalidInput


@dataclass
class Player:
    id: int | None
    name: str
    score: int = 0


@dataclass
class Game:
    code: str
    host_token: str
    phase: str = "lobby"
    players: list[Player] = field(default_factory=list)

    @classmethod
    def create(cls) -> "Game":
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        return cls("".join(secrets.choice(alphabet) for _ in range(6)), "")

    def add_player(self, name: str, player_id: int | None = None) -> Player:
        trimmed = name.strip()
        if not 1 <= len(trimmed) <= 20:
            raise InvalidInput("Name must be between 1 and 20 characters")
        if self.phase != "lobby":
            raise Conflict("Game is not accepting players")
        normalized = "".join(trimmed.lower().split())
        if any("".join(player.name.lower().split()) == normalized for player in self.players):
            raise Conflict("That name is taken. Add an initial.")
        player = Player(player_id, trimmed)
        self.players.append(player)
        return player

    def add_player_from_persistence(self, player_id: int, name: str, score: int = 0) -> Player:
        player = Player(player_id, name, score)
        self.players.append(player)
        return player
