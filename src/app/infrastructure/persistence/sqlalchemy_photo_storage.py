from sqlalchemy.orm import Session

from app.application.ports.photo_storage import PhotoStorage
from app.infrastructure.persistence.round_models import PhotoModel


class SQLAlchemyPhotoStorage(PhotoStorage):
    def __init__(self, session: Session):
        self.session = session

    def store(self, photo_id: int, data: bytes) -> None:
        photo = self.session.get(PhotoModel, photo_id)
        if photo is not None:
            photo.data = data
            self.session.commit()

    def get(self, photo_id: int) -> bytes:
        photo = self.session.get(PhotoModel, photo_id)
        if photo is None:
            raise KeyError(photo_id)
        return photo.data
