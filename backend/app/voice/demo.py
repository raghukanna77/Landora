from .base import VoiceProvider, VOICE_PROFILE
import base64

class DemoVoiceProvider(VoiceProvider):
    def briefing_text(self, project, risk, explanations) -> str:
        top = ", ".join([e["human_explanation"].replace(" is increasing","") for e in explanations[:2]]) if explanations else "moderate risk factors"
        return f"Project briefing. {project.name} is currently in the {project.current_stage} stage. Predicted delay risk is {risk['probability']:.0%}. The major drivers are {top}. Immediate officer attention is recommended."

    def synthesize(self, text: str, language: str = "en") -> dict:
        lang_map={"en":"English","hi":"Hindi","ta":"Tamil","te":"Telugu","kn":"Kannada","ml":"Malayalam","en-IN":"English","hi-IN":"Hindi"}
        lang_name=lang_map.get(language, language)
        # BHOOMI Intelligence voice profile — deep mature male, calm authority
        prefix=f""
        fake_audio = base64.b64encode(text.encode()).decode()[:120]
        return {
            "text": text,
            "language": language,
            "audio_base64": fake_audio,
            "provider":"demo",
            "voice_profile": VOICE_PROFILE,
            "note":"DEMO MODE — browser SpeechSynthesis with deep male voice profile; integrate BHASHINI for production"
        }
