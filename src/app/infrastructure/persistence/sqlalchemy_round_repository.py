from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.ports.round_repository import RoundRepository
from app.domain.round import Photo, Round
from app.infrastructure.persistence.round_models import PhotoModel, RoundModel


class SQLAlchemyRoundRepository(RoundRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, round_: Round) -> None:
        model = RoundModel(game_code=round_.game_code, number=round_.round_number, prompt=round_.prompt,
                           category=round_.category, started_at=round_.started_at,
                           duration=round_.duration, deadline=round_.deadline, open=round_.open,
                           player_ids=round_.player_ids)
        self.session.add(model)
        self.session.commit()
        round_.id = model.id
        self._sync_photos(model, round_)

    def save(self, round_: Round) -> None:
        model = self.session.get(RoundModel, round_.id)
        if model is None:
            return self.add(round_)
        model.deadline, model.open, model.player_ids = round_.deadline, round_.open, round_.player_ids
        self._sync_photos(model, round_)
        self.session.commit()

    def for_game(self, game_code: str) -> list[Round]:
        return [self._domain(model) for model in self.session.scalars(
            select(RoundModel).where(RoundModel.game_code == game_code).order_by(RoundModel.number)
        )]

    def current(self, game_code: str) -> Round | None:
        model = self.session.scalar(select(RoundModel).where(RoundModel.game_code == game_code).order_by(RoundModel.number.desc()))
        return self._domain(model) if model else None

    def _sync_photos(self, model, round_):
        model.photos.clear()
        model.photos.extend(PhotoModel(id=getattr(photo, "id", None), player_id=photo.player_id,
                                       data=photo.data, position=photo.position) for photo in round_.photos)

    @staticmethod
    def _domain(model):
        round_ = Round(model.prompt, model.player_ids, model.started_at, model.duration, model.deadline, model.open)
        round_.id, round_.round_number, round_.category = model.id, model.number, model.category
        round_.photos = []
        for item in model.photos:
            photo = Photo(item.player_id, item.data, item.position)
            photo.id = item.id
            round_.photos.append(photo)
        return round_
