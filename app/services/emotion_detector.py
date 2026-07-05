"""
Emotion Detection Service for Manosamvada.

Architecture:
    - Rule-based keyword matching (primary layer)
    - Intensity scoring per emotion category
    - Returns structured EmotionResult with label, intensity, and tone directive

Future Enhancement:
    - Replace/augment with BERT-based classifier (transformers library)
    - Fine-tune on mental health conversation datasets (e.g., DAIC-WOZ)
"""

from dataclasses import dataclass
from typing import Optional
import re


EMOTION_LEXICONS: dict[str, list[str]] = {
    "happy": [
        "happy", "joy", "excited", "great", "wonderful", "amazing", "fantastic",
        "thrilled", "delighted", "cheerful", "glad", "blessed", "grateful",
        "content", "pleased", "elated", "ecstatic", "blissful", "overjoyed",
        "good", "fine", "well", "better", "smile", "laugh", "love",
    ],
    "sad": [
        "sad", "unhappy", "depressed", "down", "low", "miserable", "gloomy",
        "hopeless", "helpless", "worthless", "empty", "lost", "lonely",
        "heartbroken", "grief", "mourning", "sorrow", "crying", "tears",
        "disappointed", "devastated", "broken", "numb", "despair", "pain",
        "suffering", "hurt", "abandoned", "rejected", "failure",
    ],
    "angry": [
        "angry", "furious", "mad", "rage", "hate", "frustrated", "annoyed",
        "irritated", "enraged", "livid", "hostile", "aggressive", "bitter",
        "resentful", "disgusted", "outraged", "fuming", "irate", "infuriated",
        "pissed", "fed up", "done", "sick of", "cant stand",
    ],
    "anxious": [
        "anxious", "anxiety", "worried", "nervous", "scared", "afraid", "fear",
        "panic", "stress", "stressed", "overwhelmed", "tense", "uneasy",
        "apprehensive", "dread", "terror", "phobia", "restless", "on edge",
        "cant breathe", "heart racing", "shaking", "trembling",
        "catastrophize", "what if", "overthinking", "spiral",
    ],
    "crisis": [
        "suicide", "suicidal", "kill myself", "end my life", "want to die",
        "self harm", "self-harm", "cut myself", "hurt myself", "no reason to live",
        "better off dead", "cant go on", "give up on life", "overdose",
        "dont want to exist", "ending it all", "not worth living",
    ],
    "neutral": [
        "okay", "alright", "fine", "normal", "usual", "regular", "nothing",
        "just", "whatever", "dont know", "not sure",
    ],
}

TONE_DIRECTIVES: dict[str, str] = {
    "happy": (
        "The user seems happy and positive. Match their energy warmly. "
        "Celebrate their good feelings, encourage them, and be uplifting."
    ),
    "sad": (
        "The user is feeling sad or low. Respond with deep empathy and compassion. "
        "Validate their feelings without minimizing them. Be gentle, patient, and supportive. "
        "Offer comfort and remind them they are not alone."
    ),
    "angry": (
        "The user is feeling angry or frustrated. Acknowledge their frustration first. "
        "Do not be dismissive. Help them feel heard. Gently guide them toward "
        "expressing their feelings constructively."
    ),
    "anxious": (
        "The user is experiencing anxiety or stress. Be calm, grounding, and reassuring. "
        "Avoid alarming language. Offer practical breathing or grounding techniques. "
        "Validate their experience without amplifying the fear."
    ),
    "crisis": (
        "CRITICAL: The user may be in crisis. Respond with extreme care and compassion. "
        "Do NOT minimize or dismiss. Express unconditional support. Strongly but gently "
        "encourage them to reach out to a crisis helpline or trusted person immediately. "
        "Provide helpline numbers. Stay present and warm."
    ),
    "neutral": (
        "The user is in a neutral state. Be friendly, warm, and conversational. "
        "Invite them to share more about how they are feeling or what is on their mind."
    ),
}


@dataclass
class EmotionResult:
    """Structured result from emotion detection."""
    label: str
    intensity: float
    secondary: Optional[str]
    tone_directive: str
    is_crisis: bool


class EmotionDetector:
    """
    Rule-based emotion detector using weighted keyword matching.

    Usage:
        detector = EmotionDetector()
        result = detector.detect("I feel so hopeless and cant go on")
        print(result.label)       # "crisis"
        print(result.is_crisis)   # True
    """

    def __init__(self):
        self._patterns: dict[str, re.Pattern] = {
            emotion: re.compile(
                r"\b(?:" + "|".join(re.escape(w) for w in words) + r")\b",
                re.IGNORECASE,
            )
            for emotion, words in EMOTION_LEXICONS.items()
        }

    def detect(self, text: str) -> EmotionResult:
        """
        Analyze text and return an EmotionResult.

        Args:
            text: User message string.

        Returns:
            EmotionResult with label, intensity, tone_directive, is_crisis.
        """
        if not text or not text.strip():
            return self._build_result("neutral", 0.1, None)

        normalized = text.lower().strip()
        scores: dict[str, float] = {}

        for emotion, pattern in self._patterns.items():
            matches = pattern.findall(normalized)
            if matches:
                unique_matches = len(set(m.lower() for m in matches))
                word_count = max(len(normalized.split()), 1)
                scores[emotion] = min(unique_matches / word_count * 3, 1.0)

        if not scores:
            return self._build_result("neutral", 0.2, None)

        if "crisis" in scores:
            return self._build_result("crisis", scores["crisis"], None)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_label, primary_score = ranked[0]
        secondary_label = ranked[1][0] if len(ranked) > 1 else None

        return self._build_result(primary_label, primary_score, secondary_label)

    def _build_result(
        self, label: str, intensity: float, secondary: Optional[str]
    ) -> EmotionResult:
        return EmotionResult(
            label=label,
            intensity=round(intensity, 3),
            secondary=secondary,
            tone_directive=TONE_DIRECTIVES.get(label, TONE_DIRECTIVES["neutral"]),
            is_crisis=(label == "crisis"),
        )


emotion_detector = EmotionDetector()
