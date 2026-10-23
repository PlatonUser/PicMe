import random
from dataclasses import dataclass
from datetime import datetime

from app.application.ports.clock import Clock
from app.application.ports.game_repository import GameRepository
from app.application.ports.photo_storage import PhotoStorage
from app.application.ports.round_repository import RoundRepository
from app.domain.errors import Conflict, Forbidden, NotFound
from app.domain.prompt import SHUFFLE, choose_prompt, custom_prompt
from app.domain.round import Round


@dataclass
class RoundResult:
    round_number: int
    prompt: str
    category: str
    upload_deadline: datetime
    phase: str
    hint: str | None = None


@dataclass
class PhotoResult:
    photo_id: int
    player_id: int
    data: bytes


@dataclass
class CloseResult:
    phase: str
    message: str | None = None
    photo: object | None = None


class RoundService:
    def __init__(self, games: GameRepository, rounds: RoundRepository, storage: PhotoStorage, clock: Clock):
        self.games = games
        self.rounds = rounds
        self.storage = storage
        self.clock = clock

    def start_round(self, code: str, host_token: str, category: str | None = None,
                    prompt: str | None = None, duration: int = 40) -> RoundResult:
        game = self._game(code)
        self._host(game, host_token)
        if game.phase != "lobby":
            raise Conflict("Game is not in the lobby")
        existing_rounds = self.rounds.for_game(code)
        used = {existing.prompt for existing in existing_rounds}
        if prompt is not None:
            picked = custom_prompt(prompt)
            if picked.text in used:
                raise Conflict("Prompt has already been used")
        else:
            selected = (category or SHUFFLE).lower()
            picked = choose_prompt(selected, used, random.choice)
        round_ = Round.start(picked.text, [player.id for player in game.players], self.clock.now(), duration)
        round_.category = picked.category
        round_.round_number = len(existing_rounds) + 1
        round_.game_code = code
        self.rounds.add(round_)
        game.phase = "uploading"
        self.games.save(game)
        return self._result(round_, "uploading")

    def upload_photo(self, code: str, player_id: int, data: bytes) -> PhotoResult:
        game = self._game(code)
        if not any(player.id == player_id for player in game.players):
            raise NotFound("Player not found")
        round_ = self.rounds.current(code)
        if round_ is None:
            raise Conflict("Time's up")
        was_uploaded = any(photo.player_id == player_id for photo in round_.photos)
        if was_uploaded and not round_.open:
            round_.open = True
        round_.upload(player_id, data, self._now(round_))
        self.rounds.save(round_)
        photo = next(photo for photo in round_.photos if photo.player_id == player_id and photo.data == data)
        photo_id = getattr(photo, "id", id(photo))
        self.storage.store(photo_id, data)
        return PhotoResult(photo_id, player_id, data)

    def check_deadline(self, code: str) -> CloseResult:
        game = self._game(code)
        round_ = self.rounds.current(code)
        if round_ is None:
            return CloseResult(game.phase)
        now = self._now(round_)
        round_.close_if_expired(now, self._shuffle)
        if round_.open:
            return CloseResult(game.phase)
        result = round_.close(now, self._shuffle)
        game.phase = result.phase
        self.rounds.save(round_)
        self.games.save(game)
        return CloseResult(result.phase, result.message, round_.photos[0] if round_.photos else None)

    def close_round(self, code: str, host_token: str) -> CloseResult:
        game = self._game(code)
        self._host(game, host_token)
        round_ = self.rounds.current(code)
        if round_ is None:
            raise Conflict("No current round")
        result = round_.close(self._now(round_), self._shuffle)
        game.phase = result.phase
        self.rounds.save(round_)
        self.games.save(game)
        return CloseResult(result.phase, result.message, round_.photos[0] if round_.photos else None)

    def extend_round(self, code: str, host_token: str) -> datetime:
        game = self._game(code)
        self._host(game, host_token)
        round_ = self.rounds.current(code)
        if round_ is None:
            raise Conflict("No current round")
        round_.extend()
        self.rounds.save(round_)
        deadline = round_.deadline
        now = self.clock.now()
        if deadline.tzinfo is None and now.tzinfo is not None:
            deadline = deadline.replace(tzinfo=now.tzinfo)
        return deadline

    def state(self, code: str) -> dict:
        game = self._game(code)
        round_ = self.rounds.current(code)
        if round_ is None:
            return {"phase": game.phase, "round": None, "photo": None, "message": None}
        result = self.check_deadline(code)
        round_ = self.rounds.current(code)
        photo = None
        if round_.photos:
            current = min(round_.photos, key=lambda item: item.position or 1)
            photo = {"id": getattr(current, "id", None), "position": current.position,
                     "total": len(round_.photos), "uploader_name": None}
        return {"phase": result.phase, "round": {"round_number": round_.round_number, "prompt": round_.prompt,
                            "category": round_.category, "hint": None,
                            "upload_deadline": round_.deadline, "server_time": self.clock.now(),
                            "uploaded_count": len(round_.photos)}, "photo": photo,
                "message": result.message}

    def image(self, photo_id: int) -> bytes:
        try:
            return self.storage.get(photo_id)
        except (KeyError, LookupError):
            raise NotFound("Photo not found")

    def _result(self, round_: Round, phase: str) -> RoundResult:
        return RoundResult(round_.round_number, round_.prompt, round_.category,
                           round_.deadline, phase)

    def _now(self, round_: Round) -> datetime:
        now = self.clock.now()
        if round_.deadline.tzinfo is None and now.tzinfo is not None:
            return now.replace(tzinfo=None)
        return now

    @staticmethod
    def _shuffle(photos):
        result = list(photos)
        random.shuffle(result)
        return result

    def _game(self, code: str):
        game = self.games.get(code)
        if game is None:
            raise NotFound("Game not found")
        return game

    @staticmethod
    def _host(game, token: str) -> None:
        if token != game.host_token:
            raise Forbidden("Invalid host token")
