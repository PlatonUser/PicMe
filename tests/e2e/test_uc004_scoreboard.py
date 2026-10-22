import os

import pytest

from tests.e2e.helpers import (
    close_uploads,
    close_voting,
    create_game,
    end_game,
    end_game_with_token,
    join,
    next_photo,
    play_again,
    play_again_with_token,
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
    cara = join(game["code"], "Cara").json()
    players = {player["name"]: player for player in (anna, ben, cara)}

        # Same votes in both rounds. A voter gets 1 point when the guess names the uploader.
    # Anna's photo: Ben->Anna (Ben +1), Cara->Ben (wrong)
    # Ben's photo:  Anna->Ben (Anna +1), Cara->Anna (wrong)
    # Cara's photo: Anna->Cara (Anna +1), Ben->Anna (wrong)
    # Per round: Anna 2, Ben 1, Cara 0. After two rounds: Anna 4, Ben 2, Cara 0 -> ranks 1, 2, 3.
    guesses_per_round = {
        "Anna": {"Ben": "Anna", "Cara": "Ben"},
        "Ben": {"Anna": "Ben", "Cara": "Anna"},
        "Cara": {"Anna": "Cara", "Ben": "Anna"},
    }
    rounds = [guesses_per_round, guesses_per_round]

    for round_number, guesses in enumerate(rounds):
        assert start_round(game, {"prompt": f"A photo prompt {round_number}"}).status_code == 201
        photos = {
            upload_photo(game["code"], player["player_id"], tiny_jpeg).json()["photo_id"]: player
            for player in players.values()
        }
        assert close_uploads(game).status_code == 200

        for position in range(3):
            uploader = photos[state(game["code"]).json()["photo"]["id"]]
            for voter_name, guessed_name in guesses[uploader["name"]].items():
                voter = players[voter_name]
                guessed = players[guessed_name]
                assert vote(game["code"], voter["player_id"], guessed["player_id"]).status_code == 201
            assert close_voting(game).status_code == 200
            if position < 2:
                assert next_photo(game).status_code == 200
        if round_number == 0:
            assert return_to_lobby(game).status_code == 200

    return game, anna, ben, cara


@pytest.mark.xfail(reason="UC-004 not implemented yet", strict=False)
def test_last_reveal_can_return_to_lobby_preserving_game_players(tiny_jpeg):
    game, anna, ben, cara = _complete_game(tiny_jpeg)

    response = return_to_lobby(game)
    body = state(game["code"]).json()

    assert response.status_code == 200
    assert response.json() == {"phase": "lobby"}
    assert body["phase"] == "lobby"
    assert {player["name"] for player in body["players"]} == {"Anna", "Ben", "Cara"}


@pytest.mark.xfail(reason="UC-004 not implemented yet", strict=False)
def test_complete_game_ends_with_points_ranked_scoreboard_and_correct_me(tiny_jpeg):
    game, anna, ben, cara = _complete_game(tiny_jpeg)

    ended = end_game(game)
    anna_scoreboard = scoreboard(game["code"], anna["player_id"])
    ben_scoreboard = scoreboard(game["code"], ben["player_id"])
    cara_scoreboard = scoreboard(game["code"], cara["player_id"])

    assert ended.status_code == 200
    assert ended.json()["phase"] == "scoreboard"
    assert anna_scoreboard.status_code == 200
    assert ben_scoreboard.status_code == 200
    assert cara_scoreboard.status_code == 200
       expected = [
        {"player_id": anna["player_id"], "name": "Anna", "points": 4, "rank": 1},
        {"player_id": ben["player_id"], "name": "Ben", "points": 2, "rank": 2},
        {"player_id": cara["player_id"], "name": "Cara", "points": 0, "rank": 3},
    ]
    assert anna_scoreboard.json()["players"] == expected
    assert ben_scoreboard.json()["players"] == expected
    assert cara_scoreboard.json()["players"] == expected
    assert anna_scoreboard.json()["me"] == expected[0]
    assert ben_scoreboard.json()["me"] == expected[1]
    assert cara_scoreboard.json()["me"] == expected[2]


@pytest.mark.xfail(reason="UC-004 not implemented yet", strict=False)
def test_state_hides_points_and_ranks_before_scoreboard(tiny_jpeg):
    game, _, _, _ = _complete_game(tiny_jpeg)

    body = state(game["code"]).json()

    assert body["phase"] == "reveal"
    assert "points" not in body
    assert "rank" not in body


@pytest.mark.xfail(reason="UC-004 not implemented yet", strict=False)
def test_play_again_preserves_players_resets_game_to_lobby_and_hides_old_scoreboard(tiny_jpeg):
    game, anna, ben, cara = _complete_game(tiny_jpeg)
    assert end_game(game).status_code == 200

    response = play_again(game)
    body = state(game["code"]).json()
    next_scoreboard = scoreboard(game["code"], anna["player_id"])

    assert response.status_code == 200
    assert response.json() == {"phase": "lobby"}
    assert body["phase"] == "lobby"
    assert {player["name"] for player in body["players"]} == {"Anna", "Ben"}
    assert body["round"] is None
    assert body["photo"] is None
    assert {player["name"] for player in body["players"]} == {"Anna", "Ben", "Cara"}
    assert next_scoreboard.status_code == 409
    assert ben["player_id"] in {player["id"] for player in body["players"]}

    assert start_round(game, {"prompt": "The next game"}).status_code == 201
    assert upload_photo(game["code"], anna["player_id"], tiny_jpeg).status_code == 201
    assert close_uploads(game).status_code == 200
    assert vote(game["code"], ben["player_id"], cara["player_id"]).status_code == 201
    assert vote(game["code"], cara["player_id"], ben["player_id"]).status_code == 201
    assert close_voting(game).status_code == 200
    assert end_game(game).status_code == 200
    next_scoreboard = scoreboard(game["code"], anna["player_id"])
    assert next_scoreboard.status_code == 200
    assert next_scoreboard.json()["players"] == [
        {"player_id": anna["player_id"], "name": "Anna", "points": 0, "rank": 1},
        {"player_id": ben["player_id"], "name": "Ben", "points": 0, "rank": 1},
        {"player_id": cara["player_id"], "name": "Cara", "points": 0, "rank": 1},
    ]


@pytest.mark.xfail(reason="UC-004 not implemented yet", strict=False)
def test_scoreboard_errors_cover_early_unknown_game_and_host_tokens(tiny_jpeg):
    game, anna, _, _ = _complete_game(tiny_jpeg)
    before = state(game["code"]).json()
    early = scoreboard(game["code"], anna["player_id"])
    after_early = state(game["code"]).json()
    unknown = scoreboard("ZZZZZZ", anna["player_id"])
    assert early.status_code == 409
    assert after_early == before
    assert unknown.status_code == 404

    before_end_errors = state(game["code"]).json()
    missing = end_game_with_token(game)
    wrong = end_game_with_token(game, "wrong-token")
    after_end_errors = state(game["code"]).json()
    assert missing.status_code == 403
    assert wrong.status_code == 403
    assert after_end_errors == before_end_errors


@pytest.mark.xfail(reason="UC-004 not implemented yet", strict=False)
def test_play_again_requires_a_valid_host_token(tiny_jpeg):
    game, _, _, _ = _complete_game(tiny_jpeg)
    assert end_game(game).status_code == 200

    before = state(game["code"]).json()
    missing = play_again_with_token(game)
    wrong = play_again_with_token(game, "wrong-token")
    after = state(game["code"]).json()

    assert missing.status_code == 403
    assert wrong.status_code == 403
    assert after == before
