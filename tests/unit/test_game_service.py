import secrets

from app.application.game_service import GameService
from tests.unit.fakes.fake_game_repository import FakeGameRepository


def test_create_game_persists_lobby_game_with_random_host_token(monkeypatch):
    repository = FakeGameRepository()
    tokens = iter(["token-one", "token-two"])
    monkeypatch.setattr(secrets, "token_urlsafe", lambda _: next(tokens))
    service = GameService(repository)

    first = service.create_game()
    second = service.create_game()

    assert first.phase == "lobby"
    assert first.host_token == "token-one"
    assert second.host_token == "token-two"
    assert first.host_token != second.host_token
    assert repository.get(first.code) is first


def test_join_game_returns_persistent_player_id_and_name():
    repository = FakeGameRepository()
    service = GameService(repository)
    game = service.create_game()

    player = service.join_game(game.code, "  Anna  ")

    assert player.id == 1
    assert player.name == "Anna"
    assert service.state(game.code)["players"] == [{"id": 1, "name": "Anna"}]


def test_read_state_has_null_round_photo_and_voting_in_lobby():
    repository = FakeGameRepository()
    service = GameService(repository)
    game = service.create_game()

    assert service.state(game.code) == {
        "code": game.code,
        "phase": "lobby",
        "players": [],
        "message": None,
        "round": None,
        "photo": None,
        "voting": None,
    }
