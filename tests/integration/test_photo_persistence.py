from fastapi.testclient import TestClient

from app.infrastructure.web.app import create_app


def create_game(client, player_names=("Anna",)):
    game = client.post("/games").json()
    players = [
        client.post(
            f"/games/{game['code']}/players",
            json={"name": name},
        ).json()
        for name in player_names
    ]
    return game, players


def start_round(client, game):
    return client.post(
        f"/games/{game['code']}/rounds",
        json={"category": "food"},
        headers={"X-Host-Token": game["host_token"]},
    )


def upload(client, game, player_id, photo):
    return client.post(
        f"/games/{game['code']}/rounds/current/photos",
        data={"player_id": str(player_id)},
        files={"photo": ("photo.jpg", photo, "image/jpeg")},
    )


def test_photo_uploaded_by_one_app_can_be_loaded_by_a_new_app(client, tiny_jpeg):
    game, players = create_game(client)
    start_round(client, game)
    photo = upload(client, game, players[0]["player_id"], tiny_jpeg).json()

    with TestClient(create_app()) as new_client:
        response = new_client.get(f"/photos/{photo['photo_id']}/image")

    assert response.status_code == 200
    assert response.content == tiny_jpeg


def test_photo_ids_are_unique_across_app_restarts(client, tiny_jpeg):
    game_one, players_one = create_game(client)
    start_round(client, game_one)
    first = upload(client, game_one, players_one[0]["player_id"], tiny_jpeg)

    with TestClient(create_app()) as new_client:
        game_two, players_two = create_game(new_client)
        start_round(new_client, game_two)
        second = upload(new_client, game_two, players_two[0]["player_id"], tiny_jpeg)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["photo_id"] != second.json()["photo_id"]


def test_replacing_a_photo_keeps_one_photo_and_returns_new_bytes(client, tiny_jpeg):
    game, players = create_game(client)
    start_round(client, game)
    first = upload(client, game, players[0]["player_id"], tiny_jpeg)
    replacement_bytes = tiny_jpeg + b"replacement"
    replacement = upload(
        client,
        game,
        players[0]["player_id"],
        replacement_bytes,
    )

    assert first.status_code == 201
    assert replacement.status_code == 201
    state = client.get(f"/games/{game['code']}/state").json()
    image = client.get(f"/photos/{replacement.json()['photo_id']}/image")

    assert state["round"]["uploaded_count"] == 1
    assert state["photo"]["total"] == 1
    assert image.status_code == 200
    assert image.content == replacement_bytes
