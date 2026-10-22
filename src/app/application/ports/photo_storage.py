from abc import ABC, abstractmethod


class PhotoStorage(ABC):
    @abstractmethod
    def store(self, photo_id: int, data: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, photo_id: int) -> bytes:
        raise NotImplementedError

