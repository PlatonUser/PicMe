from datetime import datetime, timedelta, timezone

import pytest

from tests.unit.fakes.fake_clock import FakeClock


def create_game(client, player_names=("Anna", "Ben")):
    game = client.post("/games").json()
    players = [
        client.post(
            f"/games/{game['code']}/players",
            json={"name": name},
        ).json()
        for name in player_names
    ]
    return game, players


def start_round(client, game, **body):
    return client.post(
        f"/games/{game['code']}/rounds",
        json=body,
        headers={"X-Host-Token": game["host_token"]},
    )


def upload(client, game, player_id, photo):
    return client.post(
        f"/games/{game['code']}/rounds/current/photos",
        data={"player_id": str(player_id)},
        files={"photo": ("photo.jpg", photo, "image/jpeg")},
    )


def override_clock(client, clock):
    from app.infrastructure.web.app import get_clock

    client.app.dependency_overrides[get_clock] = lambda: clock


def test_categories_returns_selectable_prompt_categories(client):
    response = client.get("/prompts/categories")

    assert response.status_code == 200
    assert {category["id"] for category in response.json()} >= {"food", "shuffle"}


@pytest.mark.parametrize("body", [{"category": "food"}, {"category": "Shuffle"}, {"prompt": "A custom prompt"}])
def test_host_starts_category_shuffle_or_custom_round(client, body):
    game, _ = create_game(client)

    response = start_round(client, game, **body)

    assert response.status_code == 201
    result = response.json()
    assert result["round_number"] == 1
    assert result["prompt"]
    assert result["upload_deadline"]
    assert result["phase"] == "uploading"


def test_round_uses_requested_duration_and_server_time(client):
    game, _ = create_game(client)
    clock = FakeClock(datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc))
    override_clock(client, clock)

    response = start_round(client, game, category="food", duration=20)

    assert response.status_code == 201
    assert response.json()["upload_deadline"] == "2026-10-22T12:00:20+00:00"


def test_round_deadlines_are_iso8601_utc_with_timezone(client):
    game, _ = create_game(client)
    clock = FakeClock(datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc))
    override_clock(client, clock)

    started = start_round(client, game, category="food", duration=20)
    extended = client.post(
        f"/games/{game['code']}/rounds/current/extend",
        headers={"X-Host-Token": game["host_token"]},
    )
    state = client.get(f"/games/{game['code']}/state")

    assert started.status_code == 201
    assert extended.status_code == 200
    assert state.status_code == 200
    deadlines = [
        started.json()["upload_deadline"],
        extended.json()["upload_deadline"],
        state.json()["round"]["upload_deadline"],
    ]
    for deadline in deadlines:
        parsed = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
        assert parsed.utcoffset() == timezone.utc.utcoffset(parsed)
        assert deadline.endswith(("Z", "+00:00"))


def test_second_round_does_not_repeat_a_used_category_prompt(client):
    game, _ = create_game(client)
    first = start_round(client, game, category="food").json()["prompt"]
    client.post(
        f"/games/{game['code']}/rounds/current/close",
        headers={"X-Host-Token": game["host_token"]},
    )
    second = start_round(client, game, category="food")

    assert second.status_code == 201
    assert second.json()["prompt"] != first


def test_shuffle_round_does_not_repeat_prompt_used_by_earlier_rounds(client):
    game, _ = create_game(client)
    used_prompts = []

    for category in ("food", "everyday", "nights"):
        response = start_round(client, game, category=category)
        assert response.status_code == 201
        used_prompts.append(response.json()["prompt"])
        closed = client.post(
            f"/games/{game['code']}/rounds/current/close",
            headers={"X-Host-Token": game["host_token"]},
        )
        assert closed.status_code == 200

    shuffled = start_round(client, game, category="Shuffle")

    assert shuffled.status_code == 201
    assert shuffled.json()["prompt"] not in used_prompts


def test_player_uploads_and_replaces_a_jpeg(client, tiny_jpeg):
    game, players = create_game(client, ("Anna",))
    start_round(client, game, category="food")

    first = upload(client, game, players[0]["player_id"], tiny_jpeg)
    replacement = upload(client, game, players[0]["player_id"], tiny_jpeg + b"replacement")

    assert first.status_code == 201
    assert replacement.status_code == 201
    assert replacement.json()["player_id"] == players[0]["player_id"]
    assert replacement.json()["photo_id"] != first.json()["photo_id"]


def test_state_read_after_deadline_moves_round_to_voting(client, tiny_jpeg):
    game, players = create_game(client, ("Anna",))
    clock = FakeClock(datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc))
    override_clock(client, clock)
    start_round(client, game, category="food", duration=20)
    upload(client, game, players[0]["player_id"], tiny_jpeg)
    clock.advance(timedelta(seconds=20))

    response = client.get(f"/games/{game['code']}/state")

    assert response.status_code == 200
    assert response.json()["phase"] == "voting"
    assert response.json()["round"]["uploaded_count"] == 1
    assert response.json()["message"] is None


def test_state_during_uploading_hides_uploaded_photo(client, tiny_jpeg):
    game, players = create_game(client)
    start_round(client, game, category="food")
    upload(client, game, players[0]["player_id"], tiny_jpeg)

    response = client.get(f"/games/{game['code']}/state")

    assert response.status_code == 200
    result = response.json()
    assert result["phase"] == "uploading"
    assert result["round"]["uploaded_count"] == 1
    assert result["photo"] is None


def test_host_extends_deadline_by_ten_seconds(client):
    game, _ = create_game(client)
    clock = FakeClock(datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc))
    override_clock(client, clock)
    start_round(client, game, category="food", duration=20)

    response = client.post(
        f"/games/{game['code']}/rounds/current/extend",
        headers={"X-Host-Token": game["host_token"]},
    )

    assert response.status_code == 200
    assert response.json()["upload_deadline"] == "2026-10-22T12:00:30+00:00"


def test_host_closes_round_with_photos_and_sets_first_current_photo(client, tiny_jpeg):
    game, players = create_game(client, ("Anna", "Ben"))
    start_round(client, game, category="food")
    upload(client, game, players[0]["player_id"], tiny_jpeg)

    response = client.post(
        f"/games/{game['code']}/rounds/current/close",
        headers={"X-Host-Token": game["host_token"]},
    )

    assert response.status_code == 200
    assert response.json() == {"phase": "voting"}
    assert client.get(f"/games/{game['code']}/state").json()["photo"]["position"] == 1


def test_host_closes_round_without_photos_and_returns_to_lobby(client):
    game, _ = create_game(client)
    start_round(client, game, category="food")

    response = client.post(
        f"/games/{game['code']}/rounds/current/close",
        headers={"X-Host-Token": game["host_token"]},
    )

    assert response.status_code == 200
    assert response.json() == {"phase": "lobby", "message": "No photos this round"}


@pytest.mark.parametrize("body", [{"category": "food"}, {"prompt": "   "}])
def test_invalid_round_start_input_returns_unprocessable_entity(client, body):
    game, _ = create_game(client)

    response = start_round(client, game, **body, duration=10)

    assert response.status_code == 422


def test_starting_round_outside_lobby_returns_conflict(client):
    game, _ = create_game(client)
    start_round(client, game, category="food")

    response = start_round(client, game, category="food")

    assert response.status_code == 409


def test_upload_after_deadline_returns_times_up(client, tiny_jpeg):
    game, players = create_game(client, ("Anna",))
    clock = FakeClock(datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc))
    override_clock(client, clock)
    start_round(client, game, category="food", duration=20)
    clock.advance(timedelta(seconds=20))

    response = upload(client, game, players[0]["player_id"], tiny_jpeg)

    assert response.status_code == 409
    assert response.json() == {"detail": "Time's up"}


@pytest.mark.parametrize("token", [None, "wrong-token"])
def test_missing_or_incorrect_host_token_returns_forbidden(client, token):
    game, _ = create_game(client)
    start_round(client, game, category="food")
    before = client.get(f"/games/{game['code']}/state").json()
    headers = {} if token is None else {"X-Host-Token": token}

    response = client.post(
        f"/games/{game['code']}/rounds",
        json={"category": "food"},
        headers=headers,
    )

    assert response.status_code == 403
    after = client.get(f"/games/{game['code']}/state").json()
    assert after["phase"] == before["phase"]
    assert {key: value for key, value in after["round"].items() if key != "server_time"} == {
        key: value for key, value in before["round"].items() if key != "server_time"
    }
    assert after["round"]["uploaded_count"] == before["round"]["uploaded_count"]


def test_unknown_game_returns_not_found(client):
    response = client.post(
        "/games/ABC234/rounds",
        json={"category": "food"},
        headers={"X-Host-Token": "token"},
    )

    assert response.status_code == 404


def test_unknown_player_returns_not_found(client, tiny_jpeg):
    game, _ = create_game(client)
    start_round(client, game, category="food")
    before = client.get(f"/games/{game['code']}/state").json()

    response = upload(client, game, 999, tiny_jpeg)

    assert response.status_code == 404
    after = client.get(f"/games/{game['code']}/state").json()
    assert after["phase"] == before["phase"]
    assert {key: value for key, value in after["round"].items() if key != "server_time"} == {
        key: value for key, value in before["round"].items() if key != "server_time"
    }
    assert after["round"]["uploaded_count"] == before["round"]["uploaded_count"]


def test_non_jpeg_upload_returns_unprocessable_entity(client):
    game, players = create_game(client, ("Anna",))
    start_round(client, game, category="food")
    before = client.get(f"/games/{game['code']}/state").json()

    response = upload(client, game, players[0]["player_id"], b"not jpeg")

    assert response.status_code == 422
    after = client.get(f"/games/{game['code']}/state").json()
    assert after["phase"] == before["phase"]
    assert {key: value for key, value in after["round"].items() if key != "server_time"} == {
        key: value for key, value in before["round"].items() if key != "server_time"
    }
    assert after["round"]["uploaded_count"] == before["round"]["uploaded_count"]


def test_upload_larger_than_two_megabytes_returns_payload_too_large(client):
    game, players = create_game(client, ("Anna",))
    start_round(client, game, category="food")
    before = client.get(f"/games/{game['code']}/state").json()

    response = upload(client, game, players[0]["player_id"], b"\xff\xd8\xff" + b"x" * (2 * 1024 * 1024))

    assert response.status_code == 413
    after = client.get(f"/games/{game['code']}/state").json()
    assert after["phase"] == before["phase"]
    assert {key: value for key, value in after["round"].items() if key != "server_time"} == {
        key: value for key, value in before["round"].items() if key != "server_time"
    }
    assert after["round"]["uploaded_count"] == before["round"]["uploaded_count"]


def test_uploading_while_game_is_in_lobby_returns_times_up(client, tiny_jpeg):
    game, players = create_game(client, ("Anna",))
    before = client.get(f"/games/{game['code']}/state").json()

    response = upload(client, game, players[0]["player_id"], tiny_jpeg)

    assert response.status_code == 409
    assert response.json() == {"detail": "Time's up"}
    after = client.get(f"/games/{game['code']}/state").json()
    assert after["phase"] == before["phase"]
    assert after["round"] == before["round"]


def test_photo_image_returns_stored_jpeg(client, tiny_jpeg):
    game, players = create_game(client, ("Anna",))
    start_round(client, game, category="food")
    photo = upload(client, game, players[0]["player_id"], tiny_jpeg).json()

    response = client.get(f"/photos/{photo['photo_id']}/image")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content == tiny_jpeg
