from dataclasses import dataclass

from app.application.ports.game_repository import GameRepository
from app.application.ports.round_repository import RoundRepository
from app.application.ports.vote_repository import VoteRepository
from app.domain.errors import Conflict, Forbidden, NotFound
from app.domain.scoring import calculate_scores, rank_scoreboard


@dataclass
class ScorePhaseResult:
    phase: str


class ScoreService:
    def __init__(self, games: GameRepository, rounds: RoundRepository, votes: VoteRepository):
        self.games = games
        self.rounds = rounds
        self.votes = votes

    def end_game(self, code: str, host_token: str) -> ScorePhaseResult:
        game = self._game(code)
        self._host(game, host_token)
        self._score_game(game, code)
        game.phase = "scoreboard"
        self.games.save(game)
        return ScorePhaseResult(game.phase)

    def return_to_lobby(self, code: str, host_token: str) -> ScorePhaseResult:
        game = self._game(code)
        self._host(game, host_token)
        if game.phase != "reveal":
            raise Conflict("Game is not in reveal phase")
        self._score_game(game, code)
        game.phase = "lobby"
        self.games.save(game)
        return ScorePhaseResult(game.phase)

    def scoreboard(self, code: str, player_id: int) -> dict:
        game = self._game(code)
        if game.phase != "scoreboard":
            raise Conflict("Game is not in scoreboard phase")
        self._score_game(game, code)
        player = next((item for item in game.players if item.id == player_id), None)
        if player is None:
            raise NotFound("Player not found")
        ranked = rank_scoreboard({item.id: item.score for item in game.players})
        names = {item.id: item.name for item in game.players}
        players = [{**entry, "name": names[entry["player_id"]]} for entry in ranked]
        me = next(entry for entry in players if entry["player_id"] == player_id)
        return {"players": players, "me": me}

    def play_again(self, code: str, host_token: str) -> ScorePhaseResult:
        game = self._game(code)
        self._host(game, host_token)
        if hasattr(self.votes, "delete_for_game"):
            self.votes.delete_for_game(code)
        else:
            self.votes.votes.clear()
        if hasattr(self.rounds, "delete_for_game"):
            self.rounds.delete_for_game(code)
        else:
            self.rounds.rounds.clear()
        for player in game.players:
            player.score = 0
        game.phase = "lobby"
        self.games.save(game)
        return ScorePhaseResult(game.phase)

    def _score_game(self, game, code: str) -> None:
        photos = []
        for round_ in self.rounds.for_game(code):
            for photo in round_.photos:
                vote = self.votes.get(photo.id)
                photos.append({"uploader_id": photo.player_id,
                               "guesses": vote.guesses if vote else {}})
        scores = calculate_scores({player.id: player.name for player in game.players}, photos)
        for player in game.players:
            player.score = scores[player.id]

    def _game(self, code):
        game = self.games.get(code)
        if game is None:
            raise NotFound("Game not found")
        return game

    @staticmethod
    def _host(game, token):
        if token != game.host_token:
            raise Forbidden("Invalid host token")
