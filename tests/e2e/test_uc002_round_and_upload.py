import os
from datetime import datetime, timedelta

import pytest

from tests.e2e.helpers import (
    close_uploads,
    create_game,
    extend_uploads,
    join,
    start_round,
    start_round_for_code,
    state,
    upload_file,
    upload_photo,
)


pytestmark = pytest.mark.skipif(
    not os.environ.get("BASE_URL"), reason="BASE_URL is not set"
)


@pytest.mark.parametrize(
    "body",
    [{"category": "food", "duration": 20}, {"category": "Shuffle"}, {"prompt": "My own text"}],
)
def test_start_round_selects_prompt_sets_deadline_and_enters_uploading(body):
    game = create_game().json()

    response = start_round(game, body)
    round_body = response.json()

    assert response.status_code == 201
    assert round_body["round_number"] == 1
    assert round_body["prompt"]
    assert round_body["upload_deadline"]
    assert round_body["phase"] == "uploading"


def test_category_or_shuffle_does_not_repeat_a_prompt_in_one_game():
    game = create_game().json()
    first = start_round(game, {"category": "food"})
    assert first.status_code == 201
    closed = close_uploads(game)
    assert closed.status_code == 200
    assert closed.json()["phase"] == "lobby"

    second = start_round(game, {"category": "food"})

    assert second.status_code == 201
    assert second.json()["prompt"] != first.json()["prompt"]


def test_player_uploads_and_replaces_jpeg_during_uploading(tiny_jpeg):
    game = create_game().json()
    player = join(game["code"], "Anna").json()
    assert start_round(game, {"prompt": "A photo prompt"}).status_code == 201

    first = upload_photo(game["code"], player["player_id"], tiny_jpeg)
    replacement = upload_photo(game["code"], player["player_id"], tiny_jpeg)

    assert first.status_code == 201
    assert replacement.status_code == 201
    assert state(game["code"]).json()["round"]["uploaded_count"] == 1


def test_upload_after_uploads_close_returns_time_up_conflict(tiny_jpeg):
    game = create_game().json()
    player = join(game["code"], "Anna").json()
    assert start_round(game, {"prompt": "A photo prompt"}).status_code == 201
    assert close_uploads(game).status_code == 200

    before = state(game["code"]).json()
    response = upload_photo(game["code"], player["player_id"], tiny_jpeg)
    after = state(game["code"]).json()

    assert response.status_code == 409
    assert response.json() == {"detail": "Time's up"}
    assert after == before


def test_host_can_extend_deadline_or_close_uploads_early():
    game = create_game().json()
    started = start_round(game, {"prompt": "A photo prompt"})
    old_deadline = datetime.fromisoformat(
        started.json()["upload_deadline"].replace("Z", "+00:00")
    )
    extended = extend_uploads(game)
    closed = close_uploads(game)

    assert extended.status_code == 200
    new_deadline = datetime.fromisoformat(
        extended.json()["upload_deadline"].replace("Z", "+00:00")
    )
    assert new_deadline == old_deadline + timedelta(seconds=10)
    assert closed.status_code == 200
    assert closed.json()["phase"] == "lobby"


def test_closing_with_photos_enters_voting_with_first_photo_current(tiny_jpeg):
    game = create_game().json()
    anna = join(game["code"], "Anna").json()
    ben = join(game["code"], "Ben").json()
    assert start_round(game, {"prompt": "A photo prompt"}).status_code == 201
    assert upload_photo(game["code"], anna["player_id"], tiny_jpeg).status_code == 201
    assert upload_photo(game["code"], ben["player_id"], tiny_jpeg).status_code == 201

    response = close_uploads(game)
    body = state(game["code"]).json()

    assert response.status_code == 200
    assert response.json()["phase"] == "voting"
    assert body["phase"] == "voting"
    assert body["photo"]["position"] == 1
    assert body["photo"]["total"] == 2


def test_closing_without_photos_returns_no_photos_message_and_lobby():
    game = create_game().json()
    assert start_round(game, {"prompt": "A photo prompt"}).status_code == 201

    response = close_uploads(game)

    assert response.status_code == 200
    assert response.json() == {"phase": "lobby", "message": "No photos this round"}


def test_wrong_or_missing_host_token_returns_403():
    game = create_game().json()
    missing = start_round_for_code(game["code"], {"prompt": "A photo prompt"})
    wrong = start_round_for_code(game["code"], {"prompt": "A photo prompt"}, "wrong-token")

    assert missing.status_code == 403
    assert wrong.status_code == 403


def test_unknown_game_returns_404():
    response = start_round_for_code("ZZZZZZ", {"prompt": "A photo prompt"}, "token")

    assert response.status_code == 404


@pytest.mark.parametrize("body", [{"prompt": ""}, {"category": "food", "duration": 10}])
def test_invalid_round_input_returns_422(body):
    game = create_game().json()

    before = state(game["code"]).json()
    response = start_round(game, body)
    after = state(game["code"]).json()

    assert response.status_code == 422
    assert after == before


def test_round_action_in_wrong_phase_returns_409():
    game = create_game().json()

    before = state(game["code"]).json()
    response = close_uploads(game)
    after = state(game["code"]).json()

    assert response.status_code == 409
    assert after == before


def test_upload_unknown_player_returns_404(tiny_jpeg):
    game = create_game().json()
    assert start_round(game, {"prompt": "A photo prompt"}).status_code == 201

    before = state(game["code"]).json()
    response = upload_photo(game["code"], 999999, tiny_jpeg)
    after = state(game["code"]).json()

    assert response.status_code == 404
    assert after == before


def test_upload_invalid_file_returns_422():
    game = create_game().json()
    player = join(game["code"], "Anna").json()
    assert start_round(game, {"prompt": "A photo prompt"}).status_code == 201

    before = state(game["code"]).json()
    response = upload_file(
        game["code"], player["player_id"], b"not a jpeg", "photo.txt", "text/plain"
    )
    after = state(game["code"]).json()

    assert response.status_code == 422
    assert after == before


def test_upload_photo_larger_than_2mb_returns_413(tiny_jpeg):
    game = create_game().json()
    player = join(game["code"], "Anna").json()
    assert start_round(game, {"prompt": "A photo prompt"}).status_code == 201

    oversized_jpeg = tiny_jpeg[:-2] + b"\x00" * (2 * 1024 * 1024) + b"\xff\xd9"
    before = state(game["code"]).json()
    response = upload_photo(game["code"], player["player_id"], oversized_jpeg)
    after = state(game["code"]).json()

    assert response.status_code == 413
    assert "detail" in response.json()
    assert after == before
