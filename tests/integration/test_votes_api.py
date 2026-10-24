def create_game(client, player_names=("Anna", "Ben", "Cara")):
    game = client.post("/games").json()
    players = [
        client.post(f"/games/{game['code']}/players", json={"name": name}).json()
        for name in player_names
    ]
    return game, players


def prepare_voting_game(client, tiny_jpeg, player_names=("Anna", "Ben", "Cara")):
    game, players = create_game(client, player_names)
    client.post(
        f"/games/{game['code']}/rounds",
        json={"prompt": "A photo prompt"},
        headers={"X-Host-Token": game["host_token"]},
    )
    photos = {}
    for player in players[:2]:
        upload = client.post(
            f"/games/{game['code']}/rounds/current/photos",
            data={"player_id": str(player["player_id"])},
            files={"photo": ("photo.jpg", tiny_jpeg, "image/jpeg")},
        )
        photos[upload.json()["photo_id"]] = player
    closed = client.post(
        f"/games/{game['code']}/rounds/current/close",
        headers={"X-Host-Token": game["host_token"]},
    )
    assert closed.status_code == 200
    return game, players, photos


def host_headers(game, token=None):
    return {"X-Host-Token": token if token is not None else game["host_token"]}


def test_submit_guess_returns_403_when_voter_is_the_uploader(client, tiny_jpeg):
    game, players, _ = prepare_voting_game(client, tiny_jpeg)
    response = client.post(
        f"/games/{game['code']}/votes",
        json={"player_id": players[0]["player_id"], "guessed_player_id": players[1]["player_id"]},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "This one's yours. Keep a straight face."}


def test_submit_guess_returns_422_when_guessed_player_is_not_in_game(client, tiny_jpeg):
    game, players, _ = prepare_voting_game(client, tiny_jpeg)
    response = client.post(
        f"/games/{game['code']}/votes",
        json={"player_id": players[2]["player_id"], "guessed_player_id": 999999},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Guessed player not found"}


def test_submit_guess_returns_409_when_not_in_voting_phase(client, tiny_jpeg):
    game, players = create_game(client)
    response = client.post(
        f"/games/{game['code']}/votes",
        json={"player_id": players[1]["player_id"], "guessed_player_id": players[0]["player_id"]},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Game is not in voting phase"}


def test_submit_guess_returns_404_for_unknown_game_or_player(client, tiny_jpeg):
    game, players, _ = prepare_voting_game(client, tiny_jpeg)
    unknown_game = client.post(
        "/games/ZZZZZZ/votes",
        json={"player_id": players[1]["player_id"], "guessed_player_id": players[0]["player_id"]},
    )
    unknown_player = client.post(
        f"/games/{game['code']}/votes",
        json={"player_id": 999999, "guessed_player_id": players[0]["player_id"]},
    )

    assert unknown_game.status_code == 404
    assert unknown_game.json() == {"detail": "Game not found"}
    assert unknown_player.status_code == 404
    assert unknown_player.json() == {"detail": "Voter not found"}


def test_host_can_read_vote_progress_during_voting(client, tiny_jpeg):
    game, players, _ = prepare_voting_game(client, tiny_jpeg)
    client.post(
        f"/games/{game['code']}/votes",
        json={"player_id": players[2]["player_id"], "guessed_player_id": players[0]["player_id"]},
    )

    response = client.get(f"/games/{game['code']}/votes/progress", headers=host_headers(game))

    assert response.status_code == 200
    assert response.json() == {"voted": 1, "eligible": 2}


def test_host_can_close_voting_and_reveal_uploader(client, tiny_jpeg):
    game, players, photos = prepare_voting_game(client, tiny_jpeg)
    state = client.get(f"/games/{game['code']}/state").json()
    uploader = photos[state["photo"]["id"]]

    response = client.post(f"/games/{game['code']}/voting/close", headers=host_headers(game))

    assert response.status_code == 200
    assert response.json() == {"phase": "reveal", "uploader_name": uploader["name"]}


def test_host_can_advance_to_the_next_photo(client, tiny_jpeg):
    game, _, _ = prepare_voting_game(client, tiny_jpeg)
    client.post(f"/games/{game['code']}/voting/close", headers=host_headers(game))

    response = client.post(f"/games/{game['code']}/photos/next", headers=host_headers(game))

    assert response.status_code == 200
    assert response.json() == {"phase": "voting", "position": 2}


def test_next_photo_on_last_photo_returns_409_and_leaves_state_unchanged(client, tiny_jpeg):
    game, _, _ = prepare_voting_game(client, tiny_jpeg, ("Anna",))
    client.post(f"/games/{game['code']}/voting/close", headers=host_headers(game))
    before = client.get(f"/games/{game['code']}/state").json()

    response = client.post(f"/games/{game['code']}/photos/next", headers=host_headers(game))
    after = client.get(f"/games/{game['code']}/state").json()

    assert response.status_code == 409
    assert response.json() == {"detail": "No next photo"}
    assert {key: value for key, value in after.items() if key != "round"} == {
        key: value for key, value in before.items() if key != "round"
    }
    assert after["round"]["uploaded_count"] == before["round"]["uploaded_count"]


def test_host_can_return_to_lobby_after_last_reveal(client, tiny_jpeg):
    game, _, _ = prepare_voting_game(client, tiny_jpeg, ("Anna",))
    client.post(f"/games/{game['code']}/voting/close", headers=host_headers(game))

    response = client.post(f"/games/{game['code']}/lobby", headers=host_headers(game))

    assert response.status_code == 200
    assert response.json() == {"phase": "lobby"}


def test_state_exposes_current_photo_and_voting_without_uploader_during_voting(client, tiny_jpeg):
    game, _, _ = prepare_voting_game(client, tiny_jpeg)
    state = client.get(f"/games/{game['code']}/state").json()

    assert state["photo"]["id"] is not None
    assert state["photo"]["position"] == 1
    assert state["photo"]["uploader_name"] is None
    assert state["voting"] == {"voted": 0, "eligible": 2}


def test_state_reveals_uploader_only_after_close(client, tiny_jpeg):
    game, players, _ = prepare_voting_game(client, tiny_jpeg)
    client.post(f"/games/{game['code']}/voting/close", headers=host_headers(game))

    state = client.get(f"/games/{game['code']}/state").json()

    assert state["phase"] == "reveal"
    assert state["photo"]["uploader_name"] in {player["name"] for player in players}


def test_missing_or_wrong_host_token_on_every_host_action_returns_403_and_preserves_state(client, tiny_jpeg):
    game, _, _ = prepare_voting_game(client, tiny_jpeg)
    before = client.get(f"/games/{game['code']}/state").json()

    for token in (None, "wrong-token"):
        for path in ("votes/progress", "voting/close", "photos/next", "lobby"):
            headers = {} if token is None else host_headers(game, token)
            response = client.get(f"/games/{game['code']}/{path}", headers=headers) if path == "votes/progress" else client.post(
                f"/games/{game['code']}/{path}", headers=headers
            )
            assert response.status_code == 403
            assert response.json() == {"detail": "Invalid host token"}

    after = client.get(f"/games/{game['code']}/state").json()
    assert after["phase"] == before["phase"]
    assert after["photo"] == before["photo"]
    assert after["voting"] == before["voting"]
