from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    @abstractmethod
    def validate(self, payload: dict) -> dict:
        pass
    @abstractmethod
    def ingest(self, payload: dict) -> dict:
        pass
