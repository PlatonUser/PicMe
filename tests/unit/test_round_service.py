from datetime import datetime, timedelta

import pytest

from app.application.round_service import RoundService
from app.domain.errors import Conflict, InvalidInput, NotFound, PayloadTooLarge
from app.domain.game import Game
from tests.unit.fakes.fake_clock import FakeClock
from tests.unit.fakes.fake_game_repository import FakeGameRepository
from tests.unit.fakes.fake_photo_storage import FakePhotoStorage
from tests.unit.fakes.fake_round_repository import FakeRoundRepository


START = datetime(2026, 10, 22, 12, 0, 0)
JPEG = b"\xff\xd8\xffphoto"


def service_with_game(player_ids=(1, 2)):
    games = FakeGameRepository()
    game = Game("ABC234", "host")
    for player_id in player_ids:
        game.add_player_from_persistence(player_id, f"Player {player_id}")
    games.add(game)
    rounds = FakeRoundRepository()
    clock = FakeClock(START)
    service = RoundService(games, rounds, FakePhotoStorage(), clock)
    return service, game, rounds, clock


def test_start_round_selects_unused_prompt_and_assigns_number_and_deadline():
    service, game, rounds, clock = service_with_game()

    result = service.start_round(game.code, "host", category="food", duration=20)

    assert result.round_number == 1
    assert result.phase == "uploading"
    assert result.upload_deadline == START + timedelta(seconds=20)
    assert rounds.rounds[0].prompt


def test_start_round_never_reuses_a_prompt_in_the_same_game():
    service, game, _, _ = service_with_game()
    first = service.start_round(game.code, "host", prompt="Use this exact prompt")
    service.close_round(game.code, "host")

    with pytest.raises(Conflict):
        service.start_round(game.code, "host", prompt=first.prompt)


def test_start_round_rejects_invalid_duration_and_empty_custom_prompt():
    service, game, _, _ = service_with_game()

    with pytest.raises(InvalidInput):
        service.start_round(game.code, "host", category="food", duration=10)
    with pytest.raises(InvalidInput):
        service.start_round(game.code, "host", prompt=" ")


def test_upload_stores_photo_and_replacement_keeps_latest_photo():
    service, game, _, _ = service_with_game((1,))
    service.start_round(game.code, "host", category="food")

    first = service.upload_photo(game.code, 1, JPEG)
    second = service.upload_photo(game.code, 1, JPEG + b"-new")

    assert first.photo_id != second.photo_id
    assert second.data == JPEG + b"-new"


def test_upload_after_deadline_raises_times_up():
    service, game, _, clock = service_with_game((1,))
    service.start_round(game.code, "host", category="food")
    clock.advance(40)

    with pytest.raises(Conflict, match=r"Time's up"):
        service.upload_photo(game.code, 1, JPEG)


def test_check_deadline_enters_voting_when_photos_exist():
    service, game, _, clock = service_with_game((1, 2))
    service.start_round(game.code, "host", category="food")
    service.upload_photo(game.code, 1, JPEG)
    clock.advance(40)

    state = service.check_deadline(game.code)

    assert state.phase == "voting"
    assert state.photo.position == 1


def test_check_deadline_returns_to_lobby_when_no_photos_exist():
    service, game, _, clock = service_with_game()
    service.start_round(game.code, "host", category="food")
    clock.advance(40)

    state = service.check_deadline(game.code)

    assert state.phase == "lobby"
    assert state.message == "No photos this round"


def test_close_assigns_fixed_positions_only_once():
    service, game, rounds, _ = service_with_game((1, 2))
    service.start_round(game.code, "host", category="food")
    service.upload_photo(game.code, 1, JPEG)
    service.upload_photo(game.code, 2, JPEG)

    first = service.close_round(game.code, "host")
    positions = [(photo.player_id, photo.position) for photo in rounds.current(game.code).photos]
    second = service.close_round(game.code, "host")

    assert first.phase == "voting"
    assert second.phase == "voting"
    assert [(photo.player_id, photo.position) for photo in rounds.current(game.code).photos] == positions


@pytest.mark.parametrize("method,args", [("start_round", ("missing", "host")), ("upload_photo", ("ABC234", 999, JPEG))])
def test_round_service_rejects_unknown_game_or_player(method, args):
    service, game, _, _ = service_with_game()

    with pytest.raises(NotFound):
        if method == "start_round":
            getattr(service, method)(*args, category="food")
        else:
            getattr(service, method)(*args)


def test_round_service_rejects_oversized_photo():
    service, game, _, _ = service_with_game((1,))
    service.start_round(game.code, "host", category="food")

    with pytest.raises(PayloadTooLarge):
        service.upload_photo(game.code, 1, b"\xff\xd8\xff" + b"x" * (2 * 1024 * 1024))
