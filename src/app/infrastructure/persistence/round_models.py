from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base


class RoundModel(Base):
    __tablename__ = "rounds"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    game_code: Mapped[str] = mapped_column(ForeignKey("games.code"), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[bool] = mapped_column(nullable=False, default=True)
    player_ids: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=list)
    current_photo_position: Mapped[int | None] = mapped_column(Integer)
    photos: Mapped[list["PhotoModel"]] = relationship(
        cascade="all, delete-orphan", order_by="PhotoModel.position"
    )


class PhotoModel(Base):
    __tablename__ = "photos"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    round_id: Mapped[int] = mapped_column(ForeignKey("rounds.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    position: Mapped[int | None] = mapped_column(Integer)
