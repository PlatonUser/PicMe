from app.application.ports.game_repository import GameRepository


class FakeGameRepository(GameRepository):
    def __init__(self):
        self.games = {}
        self.players = {}

    def add(self, game):
        self.games[game.code] = game

    def get(self, code):
        return self.games.get(code)

    def save(self, game):
        self.games[game.code] = game

    def next_player_id(self):
        player_id = len(self.players) + 1
        self.players[player_id] = True
        return player_id
