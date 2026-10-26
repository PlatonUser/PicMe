from datetime import datetime

import pytest

from app.application.score_service import ScoreService
from app.domain.errors import Conflict, Forbidden, NotFound
from app.domain.game import Game
from app.domain.round import Photo, Round
from app.domain.vote import Vote
from tests.unit.fakes.fake_game_repository import FakeGameRepository
from tests.unit.fakes.fake_round_repository import FakeRoundRepository
from tests.unit.fakes.fake_vote_repository import FakeVoteRepository


START = datetime(2026, 10, 22, 12, 0, 0)


def service_with_completed_rounds(phase="reveal"):
    games = FakeGameRepository()
    game = Game("ABC234", "host", phase)
    for player_id, name in ((1, "Anna"), (2, "Ben"), (3, "Cara"), (4, "Drew")):
        game.add_player_from_persistence(player_id, name)
    games.add(game)

    rounds = FakeRoundRepository()
    round_ = Round.start("A prompt", [1, 2, 3, 4], START)
    round_.game_code = game.code
    round_.round_number = 1
    round_.photos = [
        Photo(1, b"jpeg", 1),
        Photo(2, b"jpeg", 2),
    ]
    for photo_id, photo in enumerate(round_.photos, 1):
        photo.id = photo_id
    rounds.add(round_)

    votes = FakeVoteRepository()
    first = Vote.start(1, 1, [1, 2, 3, 4])
    first.guesses = {2: 1, 3: 1, 4: 2}
    votes.save(first)
    second = Vote.start(2, 2, [1, 2, 3, 4])
    second.guesses = {1: 2, 3: 2, 4: 3}
    votes.save(second)
    return ScoreService(games, rounds, votes), game, rounds, votes


def test_end_game_sets_scoreboard_and_scores_correct_eligible_guesses():
    service, game, _, _ = service_with_completed_rounds()

    result = service.end_game(game.code, "host")

    assert result.phase == "scoreboard"
    assert game.phase == "scoreboard"
    assert service.scoreboard(game.code, 1)["me"]["points"] == 2


def test_end_game_with_wrong_token_raises_forbidden():
    service, game, _, _ = service_with_completed_rounds()

    with pytest.raises(Forbidden):
        service.end_game(game.code, "wrong-token")


def test_scoreboard_before_scoreboard_phase_raises_conflict():
    service, game, _, _ = service_with_completed_rounds("reveal")

    with pytest.raises(Conflict):
        service.scoreboard(game.code, 1)


def test_scoreboard_for_unknown_player_raises_not_found():
    service, game, _, _ = service_with_completed_rounds("scoreboard")

    with pytest.raises(NotFound):
        service.scoreboard(game.code, 999)


def test_scoreboard_returns_full_ranked_list_and_me_with_competition_ranks():
    service, game, _, _ = service_with_completed_rounds("scoreboard")

    result = service.scoreboard(game.code, 3)

    assert result == {
        "players": [
            {"player_id": 1, "name": "Anna", "points": 2, "rank": 1},
            {"player_id": 2, "name": "Ben", "points": 1, "rank": 2},
            {"player_id": 3, "name": "Cara", "points": 1, "rank": 2},
            {"player_id": 4, "name": "Drew", "points": 0, "rank": 4},
        ],
        "me": {"player_id": 3, "name": "Cara", "points": 1, "rank": 2},
    }


def test_play_again_preserves_players_deletes_game_data_and_resets_scores():
    service, game, rounds, votes = service_with_completed_rounds("scoreboard")
    service.end_game(game.code, "host")

    result = service.play_again(game.code, "host")

    assert result.phase == "lobby"
    assert game.phase == "lobby"
    assert [(player.id, player.name) for player in game.players] == [
        (1, "Anna"), (2, "Ben"), (3, "Cara"), (4, "Drew")
    ]
    assert rounds.for_game(game.code) == []
    assert votes.votes == {}
    assert all(player.score == 0 for player in game.players)


def test_play_again_with_wrong_token_raises_forbidden():
    service, game, _, _ = service_with_completed_rounds("scoreboard")

    with pytest.raises(Forbidden):
        service.play_again(game.code, "wrong-token")


def test_returning_to_lobby_between_rounds_keeps_points():
    service, game, rounds, votes = service_with_completed_rounds("reveal")

    service.return_to_lobby(game.code, "host")
    second_round = Round.start("Another prompt", [1, 2, 3, 4], START)
    second_round.game_code = game.code
    second_round.round_number = 2
    second_round.photos = [Photo(1, b"jpeg", 1)]
    second_round.photos[0].id = 3
    rounds.add(second_round)
    second_vote = Vote.start(3, 1, [1, 2, 3, 4])
    second_vote.guesses = {2: 1}
    votes.save(second_vote)
    game.phase = "reveal"

    service.end_game(game.code, "host")

    assert service.scoreboard(game.code, 1)["me"]["points"] == 2
