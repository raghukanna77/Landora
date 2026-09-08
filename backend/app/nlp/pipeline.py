import re
from .sentiment import analyze_sentiment
from .intent import detect_intent
from .urgency import detect_urgency
from .entities import extract_entities

def analyze_grievance(text: str) -> dict:
    text = text.strip()
    sentiment, s_conf = analyze_sentiment(text)
    intent, i_conf = detect_intent(text)
    urgency, u_conf = detect_urgency(text)
    entities = extract_entities(text)
    # overall confidence average
    confidence = float((s_conf + i_conf + u_conf)/3)
    # cluster_id simple: intent + sentiment
    cluster_id = f"{intent.lower()}_{sentiment.lower()}"
    return {
        "sentiment": sentiment,
        "intent": intent,
        "urgency": urgency,
        "confidence": round(confidence,2),
        "entities": entities,
        "cluster_id": cluster_id
    }
