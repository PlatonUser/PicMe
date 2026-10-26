def create_game(client, player_names=("Anna", "Ben")):
    game = client.post("/games").json()
    players = [
        client.post(f"/games/{game['code']}/players", json={"name": name}).json()
        for name in player_names
    ]
    return game, players


def host_headers(game, token=None):
    return {} if token is None else {"X-Host-Token": token}


def complete_one_photo_reveal(client, tiny_jpeg, game=None, players=None, prompt="A photo prompt"):
    if game is None:
        game, players = create_game(client)
    client.post(
        f"/games/{game['code']}/rounds",
        json={"prompt": prompt},
        headers=host_headers(game, game["host_token"]),
    )
    for player in players[:1]:
        client.post(
            f"/games/{game['code']}/rounds/current/photos",
            data={"player_id": str(player["player_id"])},
            files={"photo": ("photo.jpg", tiny_jpeg, "image/jpeg")},
        )
    client.post(
        f"/games/{game['code']}/rounds/current/close",
        headers=host_headers(game, game["host_token"]),
    )
    client.post(
        f"/games/{game['code']}/votes",
        json={"player_id": players[1]["player_id"], "guessed_player_id": players[0]["player_id"]},
    )
    client.post(
        f"/games/{game['code']}/voting/close",
        headers=host_headers(game, game["host_token"]),
    )
    return game, players


def public_state(state):
    return {key: value for key, value in state.items() if key != "round"} | {
        "round": None if state["round"] is None else {
            key: value for key, value in state["round"].items() if key != "server_time"
        }
    }


def test_host_returns_to_lobby_after_last_reveal_preserving_scores(client, tiny_jpeg):
    game, players = complete_one_photo_reveal(client, tiny_jpeg)
    response = client.post(f"/games/{game['code']}/lobby", headers=host_headers(game, game["host_token"]))

    assert response.status_code == 200
    assert response.json() == {"phase": "lobby"}

    game, _ = complete_one_photo_reveal(
        client, tiny_jpeg, game, players, prompt="Another photo prompt"
    )
    ended = client.post(f"/games/{game['code']}/end", headers=host_headers(game, game["host_token"]))
    scoreboard = client.get(f"/games/{game['code']}/scoreboard?player_id={players[1]['player_id']}")

    assert ended.status_code == 200
    assert scoreboard.json()["me"]["points"] == 2


def test_host_can_end_game_and_read_full_scoreboard(client, tiny_jpeg):
    game, players = complete_one_photo_reveal(client, tiny_jpeg)

    ended = client.post(f"/games/{game['code']}/end", headers=host_headers(game, game["host_token"]))
    scoreboard = client.get(f"/games/{game['code']}/scoreboard?player_id={players[1]['player_id']}")

    assert ended.status_code == 200
    assert ended.json() == {"phase": "scoreboard"}
    assert scoreboard.status_code == 200
    assert scoreboard.json() == {
        "players": [
            {"player_id": players[1]["player_id"], "name": "Ben", "points": 1, "rank": 1},
            {"player_id": players[0]["player_id"], "name": "Anna", "points": 0, "rank": 2},
        ],
        "me": {"player_id": players[1]["player_id"], "name": "Ben", "points": 1, "rank": 1},
    }


def test_scoreboard_too_early_returns_409_and_state_is_unchanged(client):
    game, _ = create_game(client)
    before = public_state(client.get(f"/games/{game['code']}/state").json())

    response = client.get(f"/games/{game['code']}/scoreboard?player_id=1")

    assert response.status_code == 409
    assert response.json() == {"detail": "Game is not in scoreboard phase"}
    assert public_state(client.get(f"/games/{game['code']}/state").json()) == before


def test_unknown_game_scoreboard_end_and_play_again_return_404(client):
    for method, path, kwargs in (
        (client.get, "/games/ABC234/scoreboard?player_id=1", {}),
        (client.post, "/games/ABC234/end", {"headers": {"X-Host-Token": "host"}}),
        (client.post, "/games/ABC234/play-again", {"headers": {"X-Host-Token": "host"}}),
    ):
        response = method(path, **kwargs)
        assert response.status_code == 404
        assert response.json() == {"detail": "Game not found"}


def test_missing_or_wrong_host_tokens_for_end_and_play_again_return_403_unchanged(client, tiny_jpeg):
    game, _ = complete_one_photo_reveal(client, tiny_jpeg)
    before = public_state(client.get(f"/games/{game['code']}/state").json())

    for token in (None, "wrong-token"):
        response = client.post(f"/games/{game['code']}/end", headers=host_headers(game, token))
        assert response.status_code == 403
        assert response.json() == {"detail": "Invalid host token"}
        assert public_state(client.get(f"/games/{game['code']}/state").json()) == before

    client.post(f"/games/{game['code']}/end", headers=host_headers(game, game["host_token"]))
    before = public_state(client.get(f"/games/{game['code']}/state").json())
    for token in (None, "wrong-token"):
        response = client.post(f"/games/{game['code']}/play-again", headers=host_headers(game, token))
        assert response.status_code == 403
        assert response.json() == {"detail": "Invalid host token"}
        assert public_state(client.get(f"/games/{game['code']}/state").json()) == before


def test_play_again_resets_to_lobby_keeps_players_and_removes_round_data(client, tiny_jpeg):
    game, players = complete_one_photo_reveal(client, tiny_jpeg)
    client.post(f"/games/{game['code']}/end", headers=host_headers(game, game["host_token"]))

    response = client.post(f"/games/{game['code']}/play-again", headers=host_headers(game, game["host_token"]))
    state = client.get(f"/games/{game['code']}/state").json()

    assert response.status_code == 200
    assert response.json() == {"phase": "lobby"}
    assert [(player["id"], player["name"]) for player in state["players"]] == [
        (player["player_id"], player["name"]) for player in players
    ]
    assert state["round"] is None


def test_state_never_contains_points_or_ranks_in_any_phase(client, tiny_jpeg):
    game, _ = complete_one_photo_reveal(client, tiny_jpeg)
    states = [client.get(f"/games/{game['code']}/state").json()]
    client.post(f"/games/{game['code']}/end", headers=host_headers(game, game["host_token"]))
    states.append(client.get(f"/games/{game['code']}/state").json())
    client.post(f"/games/{game['code']}/play-again", headers=host_headers(game, game["host_token"]))
    states.append(client.get(f"/games/{game['code']}/state").json())

    for state in states:
        assert "points" not in str(state)
        assert "rank" not in str(state)
