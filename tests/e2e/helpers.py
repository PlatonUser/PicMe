import os

import httpx


def _url(path):
    return f"{os.environ['BASE_URL'].rstrip('/')}{path}"


def create_game():
    return httpx.post(_url("/games"))


def join(code, name):
    return httpx.post(_url(f"/games/{code}/players"), json={"name": name})


def start_round(game, body):
    return httpx.post(
        _url(f"/games/{game['code']}/rounds"),
        headers={"X-Host-Token": game["host_token"]},
        json=body,
    )


def upload_photo(code, player_id, jpeg_bytes):
    return httpx.post(
        _url(f"/games/{code}/rounds/current/photos"),
        data={"player_id": str(player_id)},
        files={"photo": ("photo.jpg", jpeg_bytes, "image/jpeg")},
    )


def close_uploads(game):
    return httpx.post(
        _url(f"/games/{game['code']}/rounds/current/close"),
        headers={"X-Host-Token": game["host_token"]},
    )


def vote(code, player_id, guessed_player_id):
    return httpx.post(
        _url(f"/games/{code}/votes"),
        json={"player_id": player_id, "guessed_player_id": guessed_player_id},
    )


def state(code):
    return httpx.get(_url(f"/games/{code}/state"))
