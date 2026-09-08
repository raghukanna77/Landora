INTENT_KEYWORDS = {
    "compensation": ["compensation", "payment", "paid", "money", "amount", "cheque", "compansation"],
    "ownership": ["ownership", "title", "heir", "succession", "mutation", "khata", "khasra", "survey number"],
    "consultation": ["consultation", "hearing", "meeting", "explained", "sia", "social impact", "gram sabha", "public hearing"],
    "legal": ["court", "case", "stay", "litigation", "dispute", "legal", "advocate", "petition"],
    "process": ["notification", "award", "possession", "consent", "procedure", "process", "delay", "notice"],
    "rehabilitation": ["rehabilitation", "resettlement", "r&r", "relocation", "rehab"],
    "documentation": ["document", "record", "paper", "certificate", "verification", "mismatch", "land record"],
}

def detect_intent(text: str):
    t = text.lower()
    scores={}
    for intent, kws in INTENT_KEYWORDS.items():
        scores[intent]=sum(1 for kw in kws if kw in t)
    best = max(scores, key=lambda k: scores[k])
    if scores[best]==0:
        return "other", 0.55
    conf = min(0.95, 0.6 + 0.15*scores[best])
    return best, conf
