from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable

from app.domain.errors import Conflict, InvalidInput, PayloadTooLarge


@dataclass
class Photo:
    player_id: int
    data: bytes
    position: int | None = None


@dataclass
class CloseResult:
    phase: str
    message: str | None = None


@dataclass
class Round:
    prompt: str
    player_ids: list[int]
    started_at: datetime
    duration: int
    deadline: datetime
    open: bool = True
    photos: list[Photo] = field(default_factory=list)

    @classmethod
    def start(
        cls,
        prompt: str,
        player_ids: list[int],
        started_at: datetime,
        duration: int = 40,
    ) -> "Round":
        if duration not in (20, 40, 60):
            raise InvalidInput("Duration must be 20, 40, or 60 seconds")
        return cls(
            prompt,
            player_ids,
            started_at,
            duration,
            started_at + timedelta(seconds=duration),
        )

    def extend(self) -> None:
        self.deadline += timedelta(seconds=10)

    def upload(self, player_id: int, data: bytes, now: datetime) -> None:
        if not self.open or now >= self.deadline:
            raise Conflict("Time's up")
        if not data.startswith(b"\xff\xd8\xff"):
            raise InvalidInput("Photo must be a JPEG")
        if len(data) > 2 * 1024 * 1024:
            raise PayloadTooLarge("Photo must be at most 2 MB")

        photo = Photo(player_id, data)
        self.photos = [existing for existing in self.photos if existing.player_id != player_id]
        self.photos.append(photo)
        if set(self.player_ids).issubset(photo.player_id for photo in self.photos):
            self.open = False

    def close_if_expired(self, now: datetime, shuffle: Callable[[list[Photo]], list[Photo]]) -> None:
        if self.open and now >= self.deadline:
            self.close(now, shuffle)

    def close(self, now: datetime, shuffle: Callable[[list[Photo]], list[Photo]]) -> CloseResult:
        self.open = False
        if not self.photos:
            return CloseResult("lobby", "No photos this round")
        if all(photo.position is None for photo in self.photos):
            self.photos = shuffle(self.photos)
            for position, photo in enumerate(self.photos, start=1):
                photo.position = position
        return CloseResult("voting")
