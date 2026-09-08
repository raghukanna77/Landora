HIGH_WORDS = ["urgent", "immediately", "not received", "nobody", "harassment", "threat", "court", "stay", "hunger", "protest", "block", "agitation", "deadline", "overdue", "long pending"]
MEDIUM_WORDS = ["delay", "pending", "waiting", "request", "please", "soon", "clarify", "explain"]

def detect_urgency(text:str):
    t=text.lower()
    if any(w in t for w in HIGH_WORDS):
        return "HIGH", 0.88
    if any(w in t for w in MEDIUM_WORDS):
        return "MEDIUM", 0.72
    return "LOW", 0.65
