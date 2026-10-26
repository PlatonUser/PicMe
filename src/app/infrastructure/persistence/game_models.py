from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base


class GameModel(Base):
    __tablename__ = "games"

    code: Mapped[str] = mapped_column(String(6), primary_key=True)
    host_token: Mapped[str] = mapped_column(String(255), nullable=False)
    phase: Mapped[str] = mapped_column(String(32), nullable=False, default="lobby")
    players: Mapped[list["PlayerModel"]] = relationship(
        back_populates="game", cascade="all, delete-orphan", order_by="PlayerModel.id"
    )


class PlayerModel(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    game_code: Mapped[str] = mapped_column(ForeignKey("games.code"), nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[int] = mapped_column(default=0, nullable=False)
    game: Mapped[GameModel] = relationship(back_populates="players")
