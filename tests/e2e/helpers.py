import os

import httpx


def _url(path):
    return f"{os.environ['BASE_URL'].rstrip('/')}{path}"


def create_game():
    return httpx.post(_url("/games"))


def join(code, name):
    return httpx.post(_url(f"/games/{code}/players"), json={"name": name})


def start_round(game, body):
    return start_round_for_code(game["code"], body, game["host_token"])


def start_round_for_code(code, body, token=None):
    headers = {} if token is None else {"X-Host-Token": token}
    return httpx.post(
        _url(f"/games/{code}/rounds"),
        headers=headers,
        json=body,
    )


def upload_photo(code, player_id, jpeg_bytes):
    return upload_file(code, player_id, jpeg_bytes, "photo.jpg", "image/jpeg")


def upload_file(code, player_id, file_bytes, filename, content_type):
    return httpx.post(
        _url(f"/games/{code}/rounds/current/photos"),
        data={"player_id": str(player_id)},
        files={"photo": (filename, file_bytes, content_type)},
    )


def close_uploads(game):
    return httpx.post(
        _url(f"/games/{game['code']}/rounds/current/close"),
        headers={"X-Host-Token": game["host_token"]},
    )


def extend_uploads(game):
    return httpx.post(
        _url(f"/games/{game['code']}/rounds/current/extend"),
        headers={"X-Host-Token": game["host_token"]},
    )


def vote(code, player_id, guessed_player_id):
    return httpx.post(
        _url(f"/games/{code}/votes"),
        json={"player_id": player_id, "guessed_player_id": guessed_player_id},
    )


def state(code):
    return httpx.get(_url(f"/games/{code}/state"))


def state_without_server_time(code):
    body = state(code).json()
    if body["round"] is not None:
        body["round"].pop("server_time", None)
    return body


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


def end_game_with_token(game, token=None):
    headers = {} if token is None else {"X-Host-Token": token}
    return httpx.post(_url(f"/games/{game['code']}/end"), headers=headers)


def scoreboard(code, player_id):
    return httpx.get(_url(f"/games/{code}/scoreboard"), params={"player_id": player_id})


def play_again(game):
    return httpx.post(
        _url(f"/games/{game['code']}/play-again"),
        headers={"X-Host-Token": game["host_token"]},
    )


def play_again_with_token(game, token=None):
    headers = {} if token is None else {"X-Host-Token": token}
    return httpx.post(_url(f"/games/{game['code']}/play-again"), headers=headers)
