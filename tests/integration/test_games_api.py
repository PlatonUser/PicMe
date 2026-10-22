def test_create_game_returns_join_code_host_token_and_lobby_phase(client):
    response = client.post("/games")

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"code", "host_token", "phase"}
    assert len(body["code"]) == 6
    assert body["phase"] == "lobby"
    assert body["host_token"]


def test_join_game_returns_player_id_and_trimmed_name(client):
    game = client.post("/games").json()

    response = client.post(
        f"/games/{game['code']}/players",
        json={"name": " Anna "},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Anna"
    assert isinstance(response.json()["player_id"], int)


def test_duplicate_name_is_rejected_case_and_space_insensitively(client):
    game = client.post("/games").json()
    client.post(f"/games/{game['code']}/players", json={"name": "Anna Marie"})

    response = client.post(
        f"/games/{game['code']}/players",
        json={"name": " a n n a m a r i e "},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "That name is taken. Add an initial."}


def test_joining_outside_lobby_is_rejected(client):
    game = client.post("/games").json()
    client.app.state.game_service.set_phase(game["code"], "uploading")

    response = client.post(
        f"/games/{game['code']}/players",
        json={"name": "Ben"},
    )

    assert response.status_code == 409


def test_game_state_returns_phase_names_and_null_round_photo_and_voting(client):
    game = client.post("/games").json()
    client.post(f"/games/{game['code']}/players", json={"name": "Anna"})
    client.post(f"/games/{game['code']}/players", json={"name": "Ben"})

    response = client.get(f"/games/{game['code']}/state")

    assert response.status_code == 200
    assert response.json() == {
        "code": game["code"],
        "phase": "lobby",
        "players": [{"id": 1, "name": "Anna"}, {"id": 2, "name": "Ben"}],
        "message": None,
        "round": None,
        "photo": None,
        "voting": None,
    }


def test_unknown_join_code_returns_not_found(client):
    response = client.post("/games/ABC234/players", json={"name": "Anna"})

    assert response.status_code == 404


def test_empty_name_returns_invalid_input(client):
    game = client.post("/games").json()

    response = client.post(
        f"/games/{game['code']}/players",
        json={"name": "   "},
    )

    assert response.status_code == 422


def test_too_long_name_returns_invalid_input(client):
    game = client.post("/games").json()

    response = client.post(
        f"/games/{game['code']}/players",
        json={"name": "a" * 21},
    )

    assert response.status_code == 422


def test_duplicate_name_error_has_the_contract_message(client):
    game = client.post("/games").json()
    client.post(f"/games/{game['code']}/players", json={"name": "Anna"})

    response = client.post(
        f"/games/{game['code']}/players",
        json={"name": " anna "},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "That name is taken. Add an initial."
