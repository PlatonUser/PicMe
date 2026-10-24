from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class VoteModel(Base):
    __tablename__ = "votes"
    __table_args__ = (UniqueConstraint("photo_id", "voter_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    photo_id: Mapped[int] = mapped_column(ForeignKey("photos.id"), nullable=False)
    voter_id: Mapped[int] = mapped_column(Integer, nullable=False)
    guessed_player_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
