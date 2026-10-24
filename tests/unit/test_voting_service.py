from datetime import datetime

import pytest

from app.application.voting_service import VotingService
from app.domain.errors import Conflict, Forbidden
from app.domain.game import Game
from app.domain.round import Photo, Round
from tests.unit.fakes.fake_clock import FakeClock
from tests.unit.fakes.fake_game_repository import FakeGameRepository
from tests.unit.fakes.fake_photo_storage import FakePhotoStorage
from tests.unit.fakes.fake_round_repository import FakeRoundRepository
from tests.unit.fakes.fake_vote_repository import FakeVoteRepository


START = datetime(2026, 10, 22, 12, 0, 0)


def service_with_round(photo_count=2, phase="voting"):
    games = FakeGameRepository()
    game = Game("ABC234", "host", phase)
    for player_id, name in ((1, "Anna"), (2, "Ben"), (3, "Cara")):
        game.add_player_from_persistence(player_id, name)
    games.add(game)

    round_ = Round.start("A prompt", [1, 2, 3], START)
    round_.game_code = game.code
    round_.round_number = 1
    round_.photos = [Photo(player_id, b"jpeg", position)
                     for position, player_id in enumerate((1, 2, 3)[:photo_count], 1)]
    round_.current_photo_position = 1
    rounds = FakeRoundRepository()
    rounds.add(round_)
    return (VotingService(games, rounds, FakeVoteRepository(), FakePhotoStorage(), FakeClock(START)),
            game, round_)


def test_last_eligible_vote_changes_phase_to_reveal_automatically():
    service, game, _ = service_with_round(photo_count=1)

    service.vote(game.code, 2, 1)
    result = service.vote(game.code, 3, 1)

    assert result.accepted is True
    assert game.phase == "reveal"


def test_closing_an_already_closed_photo_does_nothing():
    service, game, round_ = service_with_round(photo_count=1)
    service.close_voting(game.code, "host")

    result = service.close_voting(game.code, "host")

    assert result.phase == "reveal"
    assert game.phase == "reveal"
    assert round_.current_photo_position == 1


def test_next_photo_moves_to_voting_for_the_next_photo():
    service, game, _ = service_with_round(photo_count=2)
    service.close_voting(game.code, "host")

    result = service.next_photo(game.code, "host")

    assert result.phase == "voting"
    assert result.position == 2
    assert game.phase == "voting"


def test_next_photo_on_last_photo_raises_conflict():
    service, game, _ = service_with_round(photo_count=1)
    service.close_voting(game.code, "host")

    with pytest.raises(Conflict):
        service.next_photo(game.code, "host")


def test_return_to_lobby_after_last_reveal_sets_phase_lobby():
    service, game, _ = service_with_round(photo_count=1)
    service.close_voting(game.code, "host")

    result = service.return_to_lobby(game.code, "host")

    assert result.phase == "lobby"
    assert game.phase == "lobby"


@pytest.mark.parametrize("method", ["progress", "close_voting", "next_photo", "return_to_lobby"])
def test_every_host_action_with_wrong_token_raises_forbidden(method):
    service, game, _ = service_with_round(photo_count=2)

    with pytest.raises(Forbidden):
        getattr(service, method)(game.code, "wrong-token")


def test_voting_outside_the_voting_phase_raises_conflict():
    service, game, _ = service_with_round(phase="lobby")

    with pytest.raises(Conflict):
        service.vote(game.code, 2, 1)
