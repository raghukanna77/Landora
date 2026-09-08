from abc import ABC, abstractmethod

class VoiceProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str, language: str = "en") -> dict:
        pass

    @abstractmethod
    def briefing_text(self, project, risk, explanations) -> str:
        pass
