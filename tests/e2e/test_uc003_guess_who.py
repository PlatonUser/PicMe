import os

import httpx
import pytest

from tests.e2e.helpers import (
    close_uploads,
    close_voting,
    create_game,
    join,
    next_photo,
    start_round,
    state,
    upload_photo,
    vote,
    vote_progress,
)


pytestmark = pytest.mark.skipif(
    not os.environ.get("BASE_URL"), reason="BASE_URL is not set"
)


def _voting_game(tiny_jpeg):
    game = create_game().json()
    anna = join(game["code"], "Anna").json()
    ben = join(game["code"], "Ben").json()
    cara = join(game["code"], "Cara").json()
    assert start_round(game, {"prompt": "A photo prompt"}).status_code == 201
    anna_photo = upload_photo(game["code"], anna["player_id"], tiny_jpeg).json()
    ben_photo = upload_photo(game["code"], ben["player_id"], tiny_jpeg).json()
    assert close_uploads(game).status_code == 200
    return game, anna, ben, cara, {anna_photo["photo_id"]: anna, ben_photo["photo_id"]: ben}


def _current_photo_voter(game, players_by_photo):
    current = state(game["code"]).json()["photo"]["id"]
    uploader = players_by_photo[current]
    voter = next(player for player in players_by_photo.values() if player != uploader)
    return voter, uploader


def test_eligible_player_guess_is_recorded_and_can_be_changed(tiny_jpeg):
    game, anna, ben, cara, photos = _voting_game(tiny_jpeg)
    voter, uploader = _current_photo_voter(game, photos)
    first_guess = next(player for player in (anna, ben, cara) if player not in (voter, uploader))

    first = vote(game["code"], voter["player_id"], first_guess["player_id"])
    replacement = vote(game["code"], voter["player_id"], uploader["player_id"])

    assert first.status_code == 201
    assert replacement.status_code == 201
    assert replacement.json()["accepted"] is True


def test_vote_progress_exposes_counts_without_individual_guesses(tiny_jpeg):
    game, _, _, _, photos = _voting_game(tiny_jpeg)
    voter, uploader = _current_photo_voter(game, photos)
    assert vote(game["code"], voter["player_id"], uploader["player_id"]).status_code == 201

    response = vote_progress(game)
    body = response.json()

    assert response.status_code == 200
    assert body == {"voted": 1, "eligible": 2}
    assert "guesses" not in body


def test_last_eligible_vote_enters_reveal_and_shows_uploader(tiny_jpeg):
    game, anna, ben, cara, photos = _voting_game(tiny_jpeg)
    _, uploader = _current_photo_voter(game, photos)

    for player in (anna, ben, cara):
        if player != uploader:
            response = vote(
                game["code"], player["player_id"], uploader["player_id"]
            )
            assert response.status_code == 201

    assert state(game["code"]).json()["phase"] == "reveal"
    assert state(game["code"]).json()["photo"]["uploader_name"] == uploader["name"]


def test_host_closes_voting_with_pending_votes_and_reveals_uploader(tiny_jpeg):
    game, _, _, _, photos = _voting_game(tiny_jpeg)
    _, uploader = _current_photo_voter(game, photos)

    response = close_voting(game)

    assert response.status_code == 200
    assert response.json() == {"phase": "reveal", "uploader_name": uploader["name"]}


def test_host_advances_reveal_to_voting_for_next_photo(tiny_jpeg):
    game, _, _, _, photos = _voting_game(tiny_jpeg)
    assert close_voting(game).status_code == 200

    response = next_photo(game)

    assert response.status_code == 200
    assert response.json()["phase"] == "voting"
    assert response.json()["position"] == 2


def test_host_returns_to_lobby_after_last_photo(tiny_jpeg):
    game, _, _, _, _ = _voting_game(tiny_jpeg)
    assert close_voting(game).status_code == 200
    assert next_photo(game).status_code == 200
    assert close_voting(game).status_code == 200

    response = httpx.post(
        f"{os.environ['BASE_URL'].rstrip('/')}/games/{game['code']}/lobby",
        headers={"X-Host-Token": game["host_token"]},
    )

    assert response.status_code == 200
    assert response.json() == {"phase": "lobby"}


def test_voting_errors_cover_uploader_invalid_guess_wrong_phase_and_unknown_game(tiny_jpeg):
    game, anna, _, _, photos = _voting_game(tiny_jpeg)
    voter, uploader = _current_photo_voter(game, photos)

    own_photo = vote(game["code"], uploader["player_id"], voter["player_id"])
    invalid_guess = vote(game["code"], voter["player_id"], 999999)
    assert own_photo.status_code == 403
    assert own_photo.json() == {"detail": "This one's yours. Keep a straight face."}
    assert invalid_guess.status_code == 422

    assert close_voting(game).status_code == 200
    wrong_phase = vote(game["code"], voter["player_id"], anna["player_id"])
    unknown = vote("ZZZZZZ", voter["player_id"], anna["player_id"])
    assert wrong_phase.status_code == 409
    assert unknown.status_code == 404


def test_voting_host_actions_require_the_host_token(tiny_jpeg):
    game, _, _, _, _ = _voting_game(tiny_jpeg)
    url = f"{os.environ['BASE_URL'].rstrip('/')}/games/{game['code']}/voting/close"

    missing = httpx.post(url)
    wrong = httpx.post(url, headers={"X-Host-Token": "wrong-token"})

    assert missing.status_code == 403
    assert wrong.status_code == 403
