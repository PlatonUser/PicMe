from dataclasses import dataclass

from app.application.ports.clock import Clock
from app.application.ports.game_repository import GameRepository
from app.application.ports.photo_storage import PhotoStorage
from app.application.ports.round_repository import RoundRepository
from app.application.ports.vote_repository import VoteRepository
from app.domain.errors import Conflict, Forbidden, NotFound
from app.domain.vote import Vote


@dataclass
class VoteResult:
    accepted: bool


@dataclass
class ProgressResult:
    voted: int
    eligible: int


@dataclass
class CloseVotingResult:
    phase: str
    uploader_name: str | None = None


@dataclass
class NextPhotoResult:
    phase: str
    position: int


class VotingService:
    def __init__(self, games: GameRepository, rounds: RoundRepository,
                 votes: VoteRepository, storage: PhotoStorage, clock: Clock):
        self.games = games
        self.rounds = rounds
        self.votes = votes
        self.storage = storage
        self.clock = clock

    def vote(self, code: str, voter_id: int, guessed_player_id: int) -> VoteResult:
        game = self._game(code)
        if game.phase != "voting":
            raise Conflict("Game is not in voting phase")
        round_ = self._round(code)
        photo = self._current_photo(round_)
        photo_id = getattr(photo, "id", id(photo))
        vote = self.votes.get(photo_id)
        if vote is None:
            vote = Vote.start(photo_id, photo.player_id, [player.id for player in game.players])
        vote.cast(voter_id, guessed_player_id)
        self.votes.save(vote)
        if vote.is_complete():
            game.phase = "reveal"
            self.games.save(game)
        return VoteResult(True)

    def progress(self, code: str, host_token: str) -> ProgressResult:
        game = self._game(code)
        self._host(game, host_token)
        round_ = self._round(code)
        vote = self._vote(round_, game)
        voted, eligible = vote.progress()
        return ProgressResult(voted, eligible)

    def close_voting(self, code: str, host_token: str) -> CloseVotingResult:
        game = self._game(code)
        self._host(game, host_token)
        round_ = self._round(code)
        if game.phase == "voting":
            game.phase = "reveal"
            self.games.save(game)
        photo = self._current_photo(round_)
        uploader = next(player.name for player in game.players if player.id == photo.player_id)
        return CloseVotingResult(game.phase, uploader)

    def next_photo(self, code: str, host_token: str) -> NextPhotoResult:
        game = self._game(code)
        self._host(game, host_token)
        round_ = self._round(code)
        if game.phase != "reveal":
            raise Conflict("Game is not in reveal phase")
        round_.advance_photo()
        round_.current_photo_position = round_.current_photo_position
        self.rounds.save(round_)
        game.phase = "voting"
        self.games.save(game)
        return NextPhotoResult("voting", round_.current_photo_position)

    def return_to_lobby(self, code: str, host_token: str) -> CloseVotingResult:
        game = self._game(code)
        self._host(game, host_token)
        if game.phase != "reveal":
            raise Conflict("Game is not in reveal phase")
        game.phase = "lobby"
        self.games.save(game)
        return CloseVotingResult("lobby")

    def state(self, code: str, state: dict) -> dict:
        if state.get("photo") is None or state["round"] is None:
            state["voting"] = None
            return state
        game = self._game(code)
        round_ = self._round(code)
        photo = self._current_photo(round_)
        state["photo"].update({"id": photo.id, "position": photo.position,
                                "total": len(round_.photos), "uploader_name": None})
        if game.phase == "reveal":
            state["photo"]["uploader_name"] = next(
                player.name for player in game.players if player.id == photo.player_id
            )
        vote = self._vote(round_, game)
        voted, eligible = vote.progress()
        state["voting"] = {"voted": voted, "eligible": eligible}
        return state

    def _vote(self, round_, game):
        photo = self._current_photo(round_)
        photo_id = getattr(photo, "id", id(photo))
        vote = self.votes.get(photo_id)
        if vote is None:
            vote = Vote.start(photo_id, photo.player_id, [player.id for player in game.players])
        return vote

    def _round(self, code):
        round_ = self.rounds.current(code)
        if round_ is None or not round_.photos:
            raise Conflict("No current photo")
        return round_

    @staticmethod
    def _current_photo(round_):
        position = round_.current_photo_position or 1
        return next(photo for photo in round_.photos if photo.position == position)

    def _game(self, code):
        game = self.games.get(code)
        if game is None:
            raise NotFound("Game not found")
        return game

    @staticmethod
    def _host(game, token):
        if token != game.host_token:
            raise Forbidden("Invalid host token")
