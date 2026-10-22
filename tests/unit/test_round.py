from datetime import datetime, timedelta

import pytest

from app.domain.errors import Conflict, InvalidInput, PayloadTooLarge
from app.domain.round import Round


START = datetime(2026, 10, 22, 12, 0, 0)
JPEG = b"\xff\xd8\xff" + b"photo"


@pytest.mark.parametrize("duration", [20, 40, 60])
def test_round_accepts_only_supported_durations(duration):
    round_ = Round.start("A prompt", [1, 2], START, duration=duration)

    assert round_.duration == duration
    assert round_.deadline == START + timedelta(seconds=duration)


def test_round_defaults_to_forty_seconds():
    round_ = Round.start("A prompt", [1, 2], START)

    assert round_.duration == 40
    assert round_.deadline == START + timedelta(seconds=40)


@pytest.mark.parametrize("duration", [0, 10, 30, 61, -20, None, "40"])
def test_round_rejects_any_other_duration(duration):
    with pytest.raises(InvalidInput):
        Round.start("A prompt", [1, 2], START, duration=duration)


def test_round_uses_the_supplied_start_time_for_the_deadline():
    start = datetime(2030, 1, 2, 3, 4, 5)

    round_ = Round.start("A prompt", [1], start, duration=20)

    assert round_.deadline == datetime(2030, 1, 2, 3, 4, 25)


def test_extend_adds_ten_seconds_to_the_deadline():
    round_ = Round.start("A prompt", [1], START, duration=20)

    round_.extend()

    assert round_.deadline == START + timedelta(seconds=30)


def test_player_can_upload_a_jpeg_before_the_deadline():
    round_ = Round.start("A prompt", [1], START)

    round_.upload(1, JPEG, START + timedelta(seconds=39))

    assert len(round_.photos) == 1
    assert round_.photos[0].player_id == 1
    assert round_.photos[0].data == JPEG


def test_upload_after_the_deadline_is_rejected_with_times_up():
    round_ = Round.start("A prompt", [1], START)

    with pytest.raises(Conflict, match=r"Time's up"):
        round_.upload(1, JPEG, START + timedelta(seconds=40))


def test_upload_after_the_round_is_closed_is_rejected_with_times_up():
    round_ = Round.start("A prompt", [1, 2], START)
    round_.close(START + timedelta(seconds=1), lambda photos: photos)

    with pytest.raises(Conflict, match=r"Time's up"):
        round_.upload(1, JPEG, START + timedelta(seconds=2))


def test_uploading_again_replaces_that_players_photo():
    replacement = b"\xff\xd8\xffnew-photo"
    round_ = Round.start("A prompt", [1, 2], START)
    round_.upload(1, JPEG, START + timedelta(seconds=1))

    round_.upload(1, replacement, START + timedelta(seconds=2))

    assert len(round_.photos) == 1
    assert round_.photos[0].data == replacement


def test_photo_must_start_with_the_jpeg_signature():
    round_ = Round.start("A prompt", [1], START)

    with pytest.raises(InvalidInput):
        round_.upload(1, b"not a jpeg", START + timedelta(seconds=1))


def test_photo_must_be_at_most_two_megabytes():
    round_ = Round.start("A prompt", [1], START)

    with pytest.raises(PayloadTooLarge):
        round_.upload(1, b"\xff\xd8\xff" + b"x" * (2 * 1024 * 1024 - 2), START)


def test_deadline_closes_uploads_when_time_has_passed():
    round_ = Round.start("A prompt", [1], START)

    round_.close_if_expired(START + timedelta(seconds=41), lambda photos: photos)

    assert not round_.open


def test_uploads_close_when_every_player_has_uploaded():
    round_ = Round.start("A prompt", [1, 2], START)

    round_.upload(1, JPEG, START + timedelta(seconds=1))
    round_.upload(2, JPEG, START + timedelta(seconds=2))

    assert not round_.open


def test_host_can_close_uploads():
    round_ = Round.start("A prompt", [1, 2], START)

    round_.close(START + timedelta(seconds=1), lambda photos: photos)

    assert not round_.open


def test_closing_with_no_photos_returns_to_lobby_with_a_message():
    round_ = Round.start("A prompt", [1, 2], START)

    result = round_.close(START + timedelta(seconds=1), lambda photos: photos)

    assert result.phase == "lobby"
    assert result.message == "No photos this round"


def test_closing_assigns_positions_using_the_shuffle_function():
    round_ = Round.start("A prompt", [1, 2, 3], START)
    round_.upload(1, JPEG, START + timedelta(seconds=1))
    round_.upload(2, JPEG, START + timedelta(seconds=1))
    round_.upload(3, JPEG, START + timedelta(seconds=1))
    calls = []

    def shuffle(photos):
        calls.append(list(photos))
        return list(reversed(photos))

    result = round_.close(START + timedelta(seconds=2), shuffle)

    assert result.phase == "voting"
    assert [photo.player_id for photo in round_.photos] == [3, 2, 1]
    assert [photo.position for photo in round_.photos] == [1, 2, 3]
    assert len(calls) == 1


def test_closing_does_not_reshuffle_already_positioned_photos():
    round_ = Round.start("A prompt", [1, 2], START)
    round_.upload(1, JPEG, START + timedelta(seconds=1))
    round_.upload(2, JPEG, START + timedelta(seconds=1))
    calls = []

    def shuffle(photos):
        calls.append(True)
        return list(reversed(photos))

    round_.close(START + timedelta(seconds=2), shuffle)
    positions = [(photo.player_id, photo.position) for photo in round_.photos]
    round_.close(START + timedelta(seconds=3), shuffle)

    assert [(photo.player_id, photo.position) for photo in round_.photos] == positions
    assert len(calls) == 1
