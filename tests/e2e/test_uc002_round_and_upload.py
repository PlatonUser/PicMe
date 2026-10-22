import os

import httpx
import pytest

from tests.e2e.helpers import close_uploads, create_game, join, start_round, state, upload_photo


pytestmark = pytest.mark.skipif(
    not os.environ.get("BASE_URL"), reason="BASE_URL is not set"
)


def _host_url(game, path):
    return (
        f"{os.environ['BASE_URL'].rstrip('/')}/games/{game['code']}{path}",
        {"X-Host-Token": game["host_token"]},
    )


@pytest.mark.xfail(reason="UC-002 not implemented yet", strict=False)
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


@pytest.mark.xfail(reason="UC-002 not implemented yet", strict=False)
def test_category_or_shuffle_does_not_repeat_a_prompt_in_one_game():
    game = create_game().json()
    first = start_round(game, {"prompt": "First unique prompt"})
    assert first.status_code == 201
    close_uploads(game)
    back_to_lobby_url, headers = _host_url(game, "/lobby")
    assert httpx.post(back_to_lobby_url, headers=headers).status_code == 200

    second = start_round(game, {"prompt": "Second unique prompt"})

    assert second.status_code == 201
    assert second.json()["prompt"] != first.json()["prompt"]


@pytest.mark.xfail(reason="UC-002 not implemented yet", strict=False)
def test_player_uploads_and_replaces_jpeg_during_uploading(tiny_jpeg):
    game = create_game().json()
    player = join(game["code"], "Anna").json()
    assert start_round(game, {"prompt": "A photo prompt"}).status_code == 201

    first = upload_photo(game["code"], player["player_id"], tiny_jpeg)
    replacement = upload_photo(game["code"], player["player_id"], tiny_jpeg)

    assert first.status_code == 201
    assert replacement.status_code == 201
    assert state(game["code"]).json()["round"]["uploaded_count"] == 1


@pytest.mark.xfail(reason="UC-002 not implemented yet", strict=False)
def test_upload_after_uploads_close_returns_time_up_conflict(tiny_jpeg):
    game = create_game().json()
    player = join(game["code"], "Anna").json()
    assert start_round(game, {"prompt": "A photo prompt"}).status_code == 201
    assert close_uploads(game).status_code == 200

    response = upload_photo(game["code"], player["player_id"], tiny_jpeg)

    assert response.status_code == 409
    assert response.json() == {"detail": "Time's up"}


@pytest.mark.xfail(reason="UC-002 not implemented yet", strict=False)
def test_host_can_extend_deadline_or_close_uploads_early():
    game = create_game().json()
    assert start_round(game, {"prompt": "A photo prompt"}).status_code == 201
    extend_url, headers = _host_url(game, "/rounds/current/extend")
    extended = httpx.post(extend_url, headers=headers)
    closed = close_uploads(game)

    assert extended.status_code == 200
    assert extended.json()["upload_deadline"]
    assert closed.status_code == 200
    assert closed.json()["phase"] == "lobby"


@pytest.mark.xfail(reason="UC-002 not implemented yet", strict=False)
def test_closing_with_photos_enters_voting_with_first_photo_current(tiny_jpeg):
    game = create_game().json()
    player = join(game["code"], "Anna").json()
    assert start_round(game, {"prompt": "A photo prompt"}).status_code == 201
    assert upload_photo(game["code"], player["player_id"], tiny_jpeg).status_code == 201

    response = close_uploads(game)
    body = state(game["code"]).json()

    assert response.status_code == 200
    assert response.json()["phase"] == "voting"
    assert body["phase"] == "voting"
    assert body["photo"]["position"] == 1
    assert body["photo"]["total"] == 1


@pytest.mark.xfail(reason="UC-002 not implemented yet", strict=False)
def test_closing_without_photos_returns_no_photos_message_and_lobby():
    game = create_game().json()
    assert start_round(game, {"prompt": "A photo prompt"}).status_code == 201

    response = close_uploads(game)

    assert response.status_code == 200
    assert response.json() == {"phase": "lobby", "message": "No photos this round"}


@pytest.mark.xfail(reason="UC-002 not implemented yet", strict=False)
def test_wrong_or_missing_host_token_returns_403():
    game = create_game().json()
    url, _ = _host_url(game, "/rounds")

    missing = httpx.post(url, json={"prompt": "A photo prompt"})
    wrong = httpx.post(
        url,
        headers={"X-Host-Token": "wrong-token"},
        json={"prompt": "A photo prompt"},
    )

    assert missing.status_code == 403
    assert wrong.status_code == 403


@pytest.mark.xfail(reason="UC-002 not implemented yet", strict=False)
def test_unknown_game_returns_404():
    response = httpx.post(
        f"{os.environ['BASE_URL'].rstrip('/')}/games/ZZZZZZ/rounds",
        headers={"X-Host-Token": "token"},
        json={"prompt": "A photo prompt"},
    )

    assert response.status_code == 404


@pytest.mark.xfail(reason="UC-002 not implemented yet", strict=False)
@pytest.mark.parametrize("body", [{"prompt": ""}, {"category": "food", "duration": 10}])
def test_invalid_round_input_returns_422(body):
    game = create_game().json()

    response = start_round(game, body)

    assert response.status_code == 422


@pytest.mark.xfail(reason="UC-002 not implemented yet", strict=False)
def test_round_action_in_wrong_phase_returns_409():
    game = create_game().json()

    response = close_uploads(game)

    assert response.status_code == 409


@pytest.mark.xfail(reason="UC-002 not implemented yet", strict=False)
def test_upload_unknown_player_returns_404(tiny_jpeg):
    game = create_game().json()
    assert start_round(game, {"prompt": "A photo prompt"}).status_code == 201

    response = upload_photo(game["code"], 999999, tiny_jpeg)

    assert response.status_code == 404


@pytest.mark.xfail(reason="UC-002 not implemented yet", strict=False)
def test_upload_invalid_file_returns_422():
    game = create_game().json()
    player = join(game["code"], "Anna").json()
    assert start_round(game, {"prompt": "A photo prompt"}).status_code == 201

    response = httpx.post(
        f"{os.environ['BASE_URL'].rstrip('/')}/games/{game['code']}/rounds/current/photos",
        data={"player_id": str(player["player_id"])},
        files={"photo": ("photo.txt", b"not a jpeg", "text/plain")},
    )

    assert response.status_code == 422


@pytest.mark.xfail(reason="UC-002 not implemented yet", strict=False)
def test_upload_photo_larger_than_2mb_returns_413():
    game = create_game().json()
    player = join(game["code"], "Anna").json()
    assert start_round(game, {"prompt": "A photo prompt"}).status_code == 201

    response = upload_photo(game["code"], player["player_id"], b"\xff\xd8" + b"x" * (2 * 1024 * 1024))

    assert response.status_code == 413
