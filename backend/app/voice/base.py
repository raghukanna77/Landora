from abc import ABC, abstractmethod

class VoiceProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str, language: str = "en") -> dict:
        pass

    @abstractmethod
    def briefing_text(self, project, risk, explanations) -> str:
        pass

# TTS voice profile for BHOOMI Intelligence — deep, mature, commanding male presence
# Not a clone of any copyrighted character. Original cinematic AI personality.
VOICE_PROFILE = {
    "name": "BHOOMI Intelligence",
    "description": "Deep cinematic male narrator — calm command-center authority",
    "pitch": 0.72,  # low
    "rate": 0.92,   # moderate
    "volume": 1.0,
    "lang": "en-IN",
    "style": "authoritative, concise, professional, calm"
}

# STT / TTS provider abstraction
class SpeechToTextProvider(ABC):
    @abstractmethod
    def transcribe(self, audio: bytes, language: str) -> str:
        pass

class TextToSpeechProvider(ABC):
    @abstractmethod
    def speak(self, text: str, language: str, voice_profile: dict) -> dict:
        pass
