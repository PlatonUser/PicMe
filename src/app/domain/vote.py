from dataclasses import dataclass, field

from app.domain.errors import Forbidden, InvalidInput, NotFound


@dataclass
class Vote:
    photo_id: int
    uploader_id: int
    player_ids: set[int]
    guesses: dict[int, int] = field(default_factory=dict)

    @classmethod
    def start(cls, photo_id: int, uploader_id: int, player_ids: list[int]) -> "Vote":
        return cls(photo_id, uploader_id, set(player_ids))

    @property
    def eligible_voters(self) -> set[int]:
        return self._eligible_voter_ids()

    def _eligible_voter_ids(self) -> set[int]:
        return self.player_ids - {self.uploader_id}

    def cast(self, voter_id: int, guessed_player_id: int) -> None:
        if voter_id not in self.player_ids:
            raise NotFound("Voter not found")
        if voter_id == self.uploader_id:
            raise Forbidden("This one's yours. Keep a straight face.")
        if guessed_player_id not in self.player_ids:
            raise InvalidInput("Guessed player not found")
        self.guesses[voter_id] = guessed_player_id

    def guess_for(self, voter_id: int) -> int | None:
        return self.guesses.get(voter_id)

    def progress(self) -> tuple[int, int]:
        return len(self.guesses), len(self._eligible_voter_ids())

    def is_complete(self) -> bool:
        return len(self.guesses) == len(self._eligible_voter_ids())
