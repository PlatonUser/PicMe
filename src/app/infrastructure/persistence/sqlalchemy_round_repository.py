from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.ports.round_repository import RoundRepository
from app.domain.round import Photo, Round
from app.domain.time import as_utc
from app.infrastructure.persistence.round_models import PhotoModel, RoundModel


class SQLAlchemyRoundRepository(RoundRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, round_: Round) -> None:
        model = RoundModel(
            game_code=round_.game_code,
            number=round_.round_number,
            prompt=round_.prompt,
            category=round_.category,
            started_at=as_utc(round_.started_at),
            duration=round_.duration,
            deadline=as_utc(round_.deadline),
            open=round_.open,
            player_ids=round_.player_ids,
            current_photo_position=round_.current_photo_position,
        )
        self.session.add(model)
        self.session.commit()
        round_.id = model.id
        self._sync_photos(model, round_)
        self.session.flush()
        self._assign_photo_ids(model, round_)
        self.session.commit()

    def save(self, round_: Round) -> None:
        model = self.session.get(RoundModel, round_.id)
        if model is None:
            return self.add(round_)
        model.deadline = as_utc(round_.deadline)
        model.open = round_.open
        model.player_ids = round_.player_ids
        model.current_photo_position = round_.current_photo_position
        self._sync_photos(model, round_)
        self.session.flush()
        self._assign_photo_ids(model, round_)
        self.session.commit()

    def for_game(self, game_code: str) -> list[Round]:
        models = self.session.scalars(
            select(RoundModel)
            .where(RoundModel.game_code == game_code)
            .order_by(RoundModel.number)
        )
        return [self._to_domain(model) for model in models]

    def current(self, game_code: str) -> Round | None:
        model = self.session.scalar(
            select(RoundModel)
            .where(RoundModel.game_code == game_code)
            .order_by(RoundModel.number.desc())
        )
        return self._to_domain(model) if model else None

    def _sync_photos(self, model: RoundModel, round_: Round) -> None:
        photos_by_id = {
            photo.id: photo
            for photo in round_.photos
            if getattr(photo, "id", None) is not None
        }
        for photo_model in list(model.photos):
            photo = photos_by_id.pop(photo_model.id, None)
            if photo is None:
                self.session.delete(photo_model)
                continue
            photo_model.data = photo.data
            photo_model.position = photo.position
        model.photos.extend(
            PhotoModel(player_id=photo.player_id, data=photo.data, position=photo.position)
            for photo in round_.photos
            if getattr(photo, "id", None) is None
        )

    @staticmethod
    def _assign_photo_ids(model: RoundModel, round_: Round) -> None:
        ids_by_player = {photo_model.player_id: photo_model.id for photo_model in model.photos}
        for photo in round_.photos:
            photo.id = ids_by_player[photo.player_id]

    @staticmethod
    def _to_domain(model: RoundModel) -> Round:
        round_ = Round(model.prompt, model.player_ids, as_utc(model.started_at), model.duration,
                       as_utc(model.deadline), model.open)
        round_.id, round_.round_number, round_.category = model.id, model.number, model.category
        round_.current_photo_position = model.current_photo_position
        round_.photos = []
        for item in model.photos:
            photo = Photo(item.player_id, item.data, item.position)
            photo.id = item.id
            round_.photos.append(photo)
        return round_
