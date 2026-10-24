from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable

from app.domain.errors import Conflict, InvalidInput, PayloadTooLarge
from app.domain.time import as_utc


SUPPORTED_DURATIONS = (20, 40, 60)
JPEG_SIGNATURE = b"\xff\xd8\xff"
MAX_PHOTO_SIZE = 2 * 1024 * 1024


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
    current_photo_position: int | None = None

    @classmethod
    def start(
        cls,
        prompt: str,
        player_ids: list[int],
        started_at: datetime,
        duration: int = 40,
    ) -> "Round":
        if duration not in SUPPORTED_DURATIONS:
            raise InvalidInput("Duration must be 20, 40, or 60 seconds")
        return cls(
            prompt=prompt,
            player_ids=player_ids,
            started_at=started_at,
            duration=duration,
            deadline=started_at + timedelta(seconds=duration),
        )

    def extend(self) -> None:
        self.deadline += timedelta(seconds=10)

    def upload(self, player_id: int, data: bytes, now: datetime) -> None:
        now = as_utc(now)
        if not self.open or as_utc(now) >= as_utc(self.deadline):
            raise Conflict("Time's up")
        if not data.startswith(JPEG_SIGNATURE):
            raise InvalidInput("Photo must be a JPEG")
        if len(data) > MAX_PHOTO_SIZE:
            raise PayloadTooLarge("Photo must be at most 2 MB")

        photo = Photo(player_id=player_id, data=data)
        self.photos = [existing for existing in self.photos if existing.player_id != player_id]
        self.photos.append(photo)
        if self._all_players_uploaded():
            self.open = False

    def _all_players_uploaded(self) -> bool:
        uploaded_player_ids = {photo.player_id for photo in self.photos}
        return set(self.player_ids).issubset(uploaded_player_ids)

    def close_if_expired(self, now: datetime, shuffle: Callable[[list[Photo]], list[Photo]]) -> None:
        now = as_utc(now)
        if self.open and as_utc(now) >= as_utc(self.deadline):
            self.close(now, shuffle)

    def close(self, now: datetime, shuffle: Callable[[list[Photo]], list[Photo]]) -> CloseResult:
        now = as_utc(now)
        self.open = False
        if not self.photos:
            return CloseResult(phase="lobby", message="No photos this round")
        if self._photos_are_unpositioned():
            self.photos = shuffle(self.photos)
            for position, photo in enumerate(self.photos, start=1):
                photo.position = position
        self.current_photo_position = 1
        return CloseResult(phase="voting")

    def advance_photo(self) -> None:
        if self.current_photo_position is None or self.current_photo_position >= len(self.photos):
            raise Conflict("No next photo")
        self.current_photo_position += 1

    def _photos_are_unpositioned(self) -> bool:
        return all(photo.position is None for photo in self.photos)
