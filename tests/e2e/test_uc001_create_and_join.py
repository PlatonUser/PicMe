import os

import httpx
import pytest

from tests.e2e.helpers import create_game, join, start_round, state


pytestmark = pytest.mark.skipif(
    not os.environ.get("BASE_URL"), reason="BASE_URL is not set"
)


def test_create_game_returns_join_code_host_token_and_lobby_phase():
    response = create_game()

    assert response.status_code == 201
    body = response.json()
    assert len(body["code"]) == 6
    assert body["code"].isalnum() and body["code"].isupper()
    assert not set(body["code"]) & set("O0I1")
    assert body["host_token"]
    assert body["phase"] == "lobby"


def test_player_joins_lobby_and_receives_persistent_player_id():
    game = create_game().json()

    response = join(game["code"], "  Anna  ")
    refreshed = state(game["code"])

    assert response.status_code == 201
    assert response.json()["name"] == "Anna"
    assert response.json()["player_id"] == refreshed.json()["players"][0]["id"]


def test_duplicate_name_ignores_case_and_spaces():
    game = create_game().json()
    assert join(game["code"], "Anna Smith").status_code == 201

    response = join(game["code"], " aNnA  sMiTh ")

    assert response.status_code == 409
    assert response.json() == {"detail": "That name is taken. Add an initial."}


def test_player_cannot_join_after_game_leaves_lobby():
    game = create_game().json()
    response = start_round(game, {"prompt": "A custom prompt"})
    assert response.status_code == 201

    response = join(game["code"], "Ben")

    assert response.status_code == 409


def test_game_state_returns_phase_players_and_current_round():
    game = create_game().json()
    join(game["code"], "Anna")
    join(game["code"], "Ben")

    response = state(game["code"])
    body = response.json()

    assert response.status_code == 200
    assert body["phase"] == "lobby"
    assert {player["name"] for player in body["players"]} == {"Anna", "Ben"}
    assert body["round"] is None


def test_join_unknown_game_returns_404():
    response = join("ZZZZZZ", "Anna")

    assert response.status_code == 404


@pytest.mark.parametrize("name", ["", " " , "A" * 21])
def test_join_invalid_name_returns_422(name):
    game = create_game().json()

    response = join(game["code"], name)

    assert response.status_code == 422


def test_host_action_with_missing_or_wrong_token_returns_403():
    game = create_game().json()

    missing = httpx.post(
        f"{os.environ['BASE_URL'].rstrip('/')}/games/{game['code']}/rounds",
        json={"prompt": "A custom prompt"},
    )
    wrong = httpx.post(
        f"{os.environ['BASE_URL'].rstrip('/')}/games/{game['code']}/rounds",
        headers={"X-Host-Token": "wrong-token"},
        json={"prompt": "Another prompt"},
    )

    assert missing.status_code == 403
    assert wrong.status_code == 403
