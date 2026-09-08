from .base import VoiceProvider
import os, httpx

class BhashiniVoiceProvider(VoiceProvider):
    def briefing_text(self, project, risk, explanations) -> str:
        top = ", ".join([e["human_explanation"] for e in explanations[:2]]) if explanations else "moderate risk factors"
        return f"{project.name} in {project.district}, {project.state} is currently at {risk['risk_level']} risk during {project.current_stage} stage with predicted risk {risk['probability']:.0%}. Drivers: {top}."
    def synthesize(self, text: str, language: str="en") -> dict:
        url=os.getenv("BHASHINI_API_URL")
        key=os.getenv("BHASHINI_API_KEY")
        if not url or not key:
            # fallback to demo
            from .demo import DemoVoiceProvider
            return DemoVoiceProvider().synthesize(text, language)
        try:
            # placeholder real call
            # resp=httpx.post(f"{url}/tts", json={"text":text,"language":language}, headers={"Authorization":f"Bearer {key}"}, timeout=10)
            # return resp.json()
            raise Exception("Not implemented — BHASHINI credentials required")
        except Exception as e:
            from .demo import DemoVoiceProvider
            d=DemoVoiceProvider().synthesize(text, language)
            d["fallback_reason"]=str(e)
            return d
