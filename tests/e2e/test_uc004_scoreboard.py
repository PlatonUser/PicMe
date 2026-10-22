import os

import httpx
import pytest

from tests.e2e.helpers import (
    close_uploads,
    close_voting,
    create_game,
    end_game,
    join,
    next_photo,
    play_again,
    return_to_lobby,
    scoreboard,
    start_round,
    state,
    upload_photo,
    vote,
)


pytestmark = pytest.mark.skipif(
    not os.environ.get("BASE_URL"), reason="BASE_URL is not set"
)


def _complete_game(tiny_jpeg):
    game = create_game().json()
    anna = join(game["code"], "Anna").json()
    ben = join(game["code"], "Ben").json()
    assert start_round(game, {"category": "Shuffle"}).status_code == 201
    anna_photo = upload_photo(game["code"], anna["player_id"], tiny_jpeg).json()
    ben_photo = upload_photo(game["code"], ben["player_id"], tiny_jpeg).json()
    assert close_uploads(game).status_code == 200

    photo_to_uploader = {
        anna_photo["photo_id"]: anna,
        ben_photo["photo_id"]: ben,
    }
    for position in range(2):
        current_id = state(game["code"]).json()["photo"]["id"]
        uploader = photo_to_uploader[current_id]
        voter = ben if uploader == anna else anna
        assert vote(game["code"], voter["player_id"], uploader["player_id"]).status_code == 201
        assert close_voting(game).status_code == 200
        if position == 0:
            assert next_photo(game).status_code == 200

    return game, anna, ben


@pytest.mark.xfail(reason="UC-004 not implemented yet", strict=False)
def test_last_reveal_can_return_to_lobby_preserving_game_players(tiny_jpeg):
    game, anna, ben = _complete_game(tiny_jpeg)

    response = return_to_lobby(game)
    body = state(game["code"]).json()

    assert response.status_code == 200
    assert response.json() == {"phase": "lobby"}
    assert body["phase"] == "lobby"
    assert {player["name"] for player in body["players"]} == {"Anna", "Ben"}


@pytest.mark.xfail(reason="UC-004 not implemented yet", strict=False)
def test_complete_game_ends_with_points_ranked_scoreboard_and_correct_me(tiny_jpeg):
    game, anna, ben = _complete_game(tiny_jpeg)

    ended = end_game(game)
    anna_scoreboard = scoreboard(game["code"], anna["player_id"])
    ben_scoreboard = scoreboard(game["code"], ben["player_id"])

    assert ended.status_code == 200
    assert ended.json()["phase"] == "scoreboard"
    assert anna_scoreboard.status_code == 200
    assert ben_scoreboard.status_code == 200
    players = anna_scoreboard.json()["players"]
    assert players == sorted(players, key=lambda player: player["points"], reverse=True)
    assert anna_scoreboard.json()["me"] == next(
        player for player in players if player["player_id"] == anna["player_id"]
    )
    assert ben_scoreboard.json()["me"] == next(
        player for player in players if player["player_id"] == ben["player_id"]
    )


@pytest.mark.xfail(reason="UC-004 not implemented yet", strict=False)
def test_state_hides_points_and_ranks_before_scoreboard(tiny_jpeg):
    game, _, _ = _complete_game(tiny_jpeg)

    body = state(game["code"]).json()

    assert body["phase"] == "reveal"
    assert "points" not in body
    assert "rank" not in body


@pytest.mark.xfail(reason="UC-004 not implemented yet", strict=False)
def test_play_again_preserves_players_resets_game_to_lobby_and_hides_old_scoreboard(tiny_jpeg):
    game, anna, ben = _complete_game(tiny_jpeg)
    assert end_game(game).status_code == 200

    response = play_again(game)
    body = state(game["code"]).json()
    early_scoreboard = scoreboard(game["code"], anna["player_id"])

    assert response.status_code == 200
    assert response.json() == {"phase": "lobby"}
    assert {player["name"] for player in body["players"]} == {"Anna", "Ben"}
    assert early_scoreboard.status_code == 409
    assert ben["player_id"] in {player["id"] for player in body["players"]}


@pytest.mark.xfail(reason="UC-004 not implemented yet", strict=False)
def test_scoreboard_errors_cover_early_unknown_game_and_host_tokens(tiny_jpeg):
    game, anna, _ = _complete_game(tiny_jpeg)
    early = scoreboard(game["code"], anna["player_id"])
    unknown = scoreboard("ZZZZZZ", anna["player_id"])
    assert early.status_code == 409
    assert unknown.status_code == 404

    end_url = f"{os.environ['BASE_URL'].rstrip('/')}/games/{game['code']}/end"
    missing = httpx.post(end_url)
    wrong = httpx.post(end_url, headers={"X-Host-Token": "wrong-token"})
    assert missing.status_code == 403
    assert wrong.status_code == 403


@pytest.mark.xfail(reason="UC-004 not implemented yet", strict=False)
def test_play_again_requires_a_valid_host_token(tiny_jpeg):
    game, _, _ = _complete_game(tiny_jpeg)
    assert end_game(game).status_code == 200
    url = f"{os.environ['BASE_URL'].rstrip('/')}/games/{game['code']}/play-again"

    missing = httpx.post(url)
    wrong = httpx.post(url, headers={"X-Host-Token": "wrong-token"})

    assert missing.status_code == 403
    assert wrong.status_code == 403
