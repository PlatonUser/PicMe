class FakePhotoStorage:
    def __init__(self):
        self.photos = {}

    def store(self, photo_id, data):
        self.photos[photo_id] = data

    def get(self, photo_id):
        return self.photos[photo_id]
