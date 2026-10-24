from datetime import datetime, timezone


def as_utc(value: datetime) -> datetime:
    """Return a timezone-aware UTC datetime, treating naive values as UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
