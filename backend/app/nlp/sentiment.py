NEGATIVE_WORDS = ["not", "no", "never", "delay", "pending", "unpaid", "unfair", "corrupt", "angry", "frustrated", "complaint", "grievance", "issue", "problem", "oppose", "reject", "inadequate", "insufficient", "failed", "lack", "haven't", "hasn't", "without", "against"]
POSITIVE_WORDS = ["thank", "satisfied", "happy", "resolved", "complete", "received", "appreciate", "good", "great", "approved"]

def analyze_sentiment(text: str):
    t = text.lower()
    neg = sum(1 for w in NEGATIVE_WORDS if w in t)
    pos = sum(1 for w in POSITIVE_WORDS if w in t)
    if neg > pos:
        conf = min(0.95, 0.6 + 0.1*neg)
        return "NEGATIVE", conf
    if pos > neg:
        conf = min(0.95, 0.6 + 0.1*pos)
        return "POSITIVE", conf
    # if contains question/neutral complaint without strong words, treat as negative if contains compensation etc.
    if "compensation" in t or "not received" in t:
        return "NEGATIVE", 0.75
    return "NEUTRAL", 0.65
