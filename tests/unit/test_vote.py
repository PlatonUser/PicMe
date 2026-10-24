import pytest

from app.domain.errors import Forbidden, InvalidInput, NotFound
from app.domain.vote import Vote


def voting_for_photo(uploader_id=1, player_ids=(1, 2, 3)):
    return Vote.start(photo_id=10, uploader_id=uploader_id, player_ids=list(player_ids))


def test_eligible_voters_are_all_players_except_the_uploader():
    vote = voting_for_photo()

    assert vote.eligible_voters == {2, 3}


def test_uploader_cannot_guess_their_own_photo():
    vote = voting_for_photo()

    with pytest.raises(Forbidden, match=r"This one's yours\. Keep a straight face\."):
        vote.cast(voter_id=1, guessed_player_id=2)


def test_guess_must_name_a_player_in_the_game():
    vote = voting_for_photo()

    with pytest.raises(InvalidInput):
        vote.cast(voter_id=2, guessed_player_id=99)


def test_voter_must_be_in_the_game():
    vote = voting_for_photo()

    with pytest.raises(NotFound):
        vote.cast(voter_id=99, guessed_player_id=2)


def test_voter_keeps_only_the_latest_guess_for_the_photo():
    vote = voting_for_photo()
    vote.cast(voter_id=2, guessed_player_id=1)

    vote.cast(voter_id=2, guessed_player_id=3)

    assert vote.guess_for(voter_id=2) == 3
    assert vote.progress() == (1, 2)


def test_progress_returns_only_voted_count_and_eligible_total():
    vote = voting_for_photo()
    vote.cast(voter_id=2, guessed_player_id=3)

    progress = vote.progress()

    assert progress == (1, 2)
    assert not hasattr(progress, "guesses")
    assert not hasattr(progress, "voters")


def test_voting_is_complete_when_every_eligible_voter_has_guessed():
    vote = voting_for_photo()
    vote.cast(voter_id=2, guessed_player_id=1)
    assert not vote.is_complete()

    vote.cast(voter_id=3, guessed_player_id=2)

    assert vote.is_complete()
