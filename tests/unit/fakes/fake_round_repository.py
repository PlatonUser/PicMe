class FakeRoundRepository:
    def __init__(self):
        self.rounds = []

    def add(self, round_):
        self.rounds.append(round_)

    def save(self, round_):
        if round_ not in self.rounds:
            self.rounds.append(round_)

    def for_game(self, code):
        return list(self.rounds)

    def current(self, code):
        return self.rounds[-1] if self.rounds else None
