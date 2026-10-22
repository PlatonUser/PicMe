from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.ports.game_repository import GameRepository
from app.domain.game import Game
from app.infrastructure.persistence.game_models import GameModel, PlayerModel


class SQLAlchemyGameRepository(GameRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, game: Game) -> None:
        self.session.add(GameModel(code=game.code, host_token=game.host_token, phase=game.phase))
        self.session.commit()

    def get(self, code: str) -> Game | None:
        model = self.session.get(GameModel, code)
        if model is None:
            return None
        game = Game(model.code, model.host_token, model.phase)
        for player in model.players:
            game.add_player_from_persistence(player.id, player.name)
        return game

    def save(self, game: Game) -> None:
        model = self.session.get(GameModel, game.code)
        model.phase = game.phase
        model.players.clear()
        model.players.extend(
            PlayerModel(id=player.id, name=player.name, game_code=game.code)
            for player in game.players
        )
        self.session.commit()

    def next_player_id(self) -> int:
        return (self.session.scalar(select(func.max(PlayerModel.id))) or 0) + 1
