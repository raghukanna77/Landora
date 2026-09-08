from .base import VoiceProvider
import base64

class DemoVoiceProvider(VoiceProvider):
    def briefing_text(self, project, risk, explanations) -> str:
        top = ", ".join([e["human_explanation"] for e in explanations[:2]]) if explanations else "moderate risk factors"
        return f"{project.name} in {project.district}, {project.state} is currently at {risk['risk_level']} risk of delay during the {project.current_stage} stage with predicted risk {risk['probability']:.0%}. The main drivers are {top}. The recommended action will be displayed in the decision panel."
    
    def synthesize(self, text: str, language: str = "en") -> dict:
        # demo: return pseudo audio as base64 of text
        lang_map={"en":"English","hi":"Hindi","ta":"Tamil"}
        lang_name=lang_map.get(language, language)
        prefix=f"[{lang_name} DEMO VOICE] "
        # In demo we don't generate real audio, return text and fake url
        fake_audio = base64.b64encode(text.encode()).decode()[:100]
        return {"text": prefix+text, "language": language, "audio_base64": fake_audio, "provider":"demo", "note":"DEMO MODE — no real TTS; integrate BHASHINI for production"}
