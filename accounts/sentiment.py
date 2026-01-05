# accounts/sentiment.py
from dataclasses import dataclass

AR_POS = [
    "مرتاح", "سعيد", "مبسوط", "ممتاز", "الحمد", "ثقة", "اطمئن", "مبروك", "فزنا", "نجح", "تمام",
]
AR_NEG = [
    "خايف", "قلق", "متوتر", "مضغوط", "حزين", "مكتئب", "منهار", "مستاء", "غضبان", "زعلان", "مشكلة", "تهديد",
]

EN_POS = ["happy", "great", "good", "relieved", "excellent", "win", "won", "congrats"]
EN_NEG = ["sad", "angry", "stressed", "anxious", "fear", "worried", "problem", "threat"]


@dataclass
class SentimentResult:
    label: str  # positive / neutral / negative
    score: int
    positives: int
    negatives: int


def analyze_sentiment(text: str) -> SentimentResult:
    t = (text or "").lower()
    pos = 0
    neg = 0

    for w in AR_POS:
        if w in t:
            pos += 1
    for w in AR_NEG:
        if w in t:
            neg += 1
    for w in EN_POS:
        if w in t:
            pos += 1
    for w in EN_NEG:
        if w in t:
            neg += 1

    score = pos - neg
    if score >= 2:
        label = "positive"
    elif score <= -2:
        label = "negative"
    else:
        label = "neutral"

    return SentimentResult(label=label, score=score, positives=pos, negatives=neg)
