import re

import pytest

from app.domain.errors import Conflict, InvalidInput
from app.domain.game import Game


def test_join_code_is_six_readable_characters():
    game = Game.create()

    assert re.fullmatch(r"[A-HJ-NP-Z2-9]{6}", game.code)


@pytest.mark.parametrize("name", ["", "   ", "a" * 21, "  " + "a" * 21 + "  "])
def test_player_name_must_be_trimmed_and_between_one_and_twenty_characters(name):
    game = Game.create()

    with pytest.raises(InvalidInput):
        game.add_player(name)


def test_player_name_is_trimmed_when_added():
    game = Game.create()

    player = game.add_player("  Anna  ")

    assert player.name == "Anna"


def test_player_names_are_unique_ignoring_case_and_spaces():
    game = Game.create()
    game.add_player("Anna Marie")

    with pytest.raises(Conflict, match="That name is taken. Add an initial."):
        game.add_player(" aNnA mArIe ")


def test_players_can_join_only_in_lobby():
    game = Game.create()
    game.phase = "uploading"

    with pytest.raises(Conflict):
        game.add_player("Anna")
