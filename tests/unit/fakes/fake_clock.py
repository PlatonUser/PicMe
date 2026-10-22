from datetime import datetime, timedelta


class FakeClock:
    def __init__(self, current: datetime):
        self.current = current

    def now(self):
        return self.current

    def advance(self, seconds: int | timedelta):
        self.current += (
            seconds if isinstance(seconds, timedelta) else timedelta(seconds=seconds)
        )
