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


def close_voting(game):
    return httpx.post(
        _url(f"/games/{game['code']}/voting/close"),
        headers={"X-Host-Token": game["host_token"]},
    )


def vote_progress(code):
    return httpx.get(_url(f"/games/{code}/votes/progress"))


def next_photo(game):
    return httpx.post(
        _url(f"/games/{game['code']}/photos/next"),
        headers={"X-Host-Token": game["host_token"]},
    )


def return_to_lobby(game):
    return httpx.post(
        _url(f"/games/{game['code']}/lobby"),
        headers={"X-Host-Token": game["host_token"]},
    )


def end_game(game):
    return httpx.post(
        _url(f"/games/{game['code']}/end"),
        headers={"X-Host-Token": game["host_token"]},
    )


def scoreboard(code, player_id):
    return httpx.get(_url(f"/games/{code}/scoreboard"), params={"player_id": player_id})


def play_again(game):
    return httpx.post(
        _url(f"/games/{game['code']}/play-again"),
        headers={"X-Host-Token": game["host_token"]},
    )
