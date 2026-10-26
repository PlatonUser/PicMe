from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.application.ports.vote_repository import VoteRepository
from app.domain.vote import Vote
from app.infrastructure.persistence.round_models import PhotoModel, RoundModel
from app.infrastructure.persistence.vote_models import VoteModel


class SQLAlchemyVoteRepository(VoteRepository):
    def __init__(self, session: Session):
        self.session = session

    def get(self, photo_id: int) -> Vote | None:
        vote_rows = list(
            self.session.scalars(
                select(VoteModel).where(VoteModel.photo_id == photo_id)
            )
        )
        if not vote_rows:
            return None
        uploader_id, player_ids = self.session.execute(
            select(PhotoModel.player_id, RoundModel.player_ids)
            .join(RoundModel, PhotoModel.round_id == RoundModel.id)
            .where(PhotoModel.id == photo_id)
        ).one()
        vote = Vote.start(photo_id, uploader_id, player_ids)
        vote.guesses = {
            row.voter_id: row.guessed_player_id for row in vote_rows
        }
        return vote

    def save(self, vote: Vote) -> None:
        self.session.execute(delete(VoteModel).where(VoteModel.photo_id == vote.photo_id))
        now = datetime.now(timezone.utc)
        self.session.add_all(
            VoteModel(
                photo_id=vote.photo_id,
                voter_id=voter_id,
                guessed_player_id=guessed_player_id,
                created_at=now,
            )
            for voter_id, guessed_player_id in vote.guesses.items()
        )
        self.session.commit()

    def delete_for_game(self, game_code: str) -> None:
        self.session.execute(
            delete(VoteModel).where(VoteModel.photo_id.in_(
                select(PhotoModel.id).join(RoundModel).where(RoundModel.game_code == game_code)
            ))
        )
        self.session.commit()
