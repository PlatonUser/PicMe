class FakeVoteRepository:
    def __init__(self):
        self.votes = {}

    def get(self, photo_id):
        return self.votes.get(photo_id)

    def save(self, vote):
        self.votes[vote.photo_id] = vote
