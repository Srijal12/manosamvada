"""
Unit tests for the rule-based EmotionDetector.
Run with: pytest tests/test_emotion.py -v
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.emotion_detector import EmotionDetector


detector = EmotionDetector()


def test_happy_detection():
    result = detector.detect("I feel so happy and grateful today, everything is wonderful!")
    assert result.label == "happy"
    assert result.is_crisis is False


def test_sad_detection():
    result = detector.detect("I feel so hopeless and empty, nothing seems to matter anymore")
    assert result.label == "sad"
    assert result.is_crisis is False


def test_anxious_detection():
    result = detector.detect("I'm so anxious and overwhelmed, I can't stop worrying")
    assert result.label == "anxious"


def test_angry_detection():
    result = detector.detect("I am so furious and frustrated with everything right now")
    assert result.label == "angry"


def test_crisis_detection_overrides_other_emotions():
    result = detector.detect("I feel so sad, honestly I just want to end my life")
    assert result.label == "crisis"
    assert result.is_crisis is True


def test_neutral_fallback_for_empty_text():
    result = detector.detect("")
    assert result.label == "neutral"


def test_neutral_for_unrecognized_text():
    result = detector.detect("The weather report mentioned rain tomorrow")
    assert result.label == "neutral"


def test_tone_directive_present_for_every_label():
    for text in ["happy day", "so sad", "furious now", "very anxious", "suicide", "hello"]:
        result = detector.detect(text)
        assert isinstance(result.tone_directive, str)
        assert len(result.tone_directive) > 0
