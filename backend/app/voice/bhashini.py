from .base import VoiceProvider, VOICE_PROFILE
import os

class BhashiniVoiceProvider(VoiceProvider):
    def briefing_text(self, project, risk, explanations) -> str:
        top = ", ".join([e["human_explanation"].replace(" is increasing","") for e in explanations[:2]]) if explanations else "moderate risk factors"
        return f"Project briefing. {project.name} is currently in the {project.current_stage} stage. Predicted delay risk is {risk['probability']:.0%}. The major drivers are {top}. Immediate officer attention is recommended."
    def synthesize(self, text: str, language: str="en") -> dict:
        url=os.getenv("BHASHINI_API_URL")
        key=os.getenv("BHASHINI_API_KEY")
        lang_map={"en":"en","en-IN":"en","hi":"hi","hi-IN":"hi","ta":"ta","ta-IN":"ta","te":"te","kn":"kn","ml":"ml"}
        bhashini_lang=lang_map.get(language, "en")
        if not url or not key:
            from .demo import DemoVoiceProvider
            return DemoVoiceProvider().synthesize(text, language)
        try:
            # Real BHASHINI TTS call would be here:
            # resp=httpx.post(f"{url}/tts", json={"text":text,"language":bhashini_lang,"voice":"deep-male"}, headers={"Authorization":f"Bearer {key}"}, timeout=10)
            raise Exception("BHASHINI credentials present but TTS endpoint not configured — using demo profile")
        except Exception as e:
            from .demo import DemoVoiceProvider
            d=DemoVoiceProvider().synthesize(text, language)
            d["fallback_reason"]=str(e)
            d["voice_profile"]=VOICE_PROFILE
            return d
