"""
Unit tests for the CrisisService keyword fallback matching.
Run with: pytest tests/test_crisis.py -v

Note: these tests exercise the in-memory fallback keyword list directly,
since the database-backed path requires an app context and a live MySQL
connection (see tests/test_auth.py for an app-context example).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import re
from app.services.crisis_service import CrisisService


service = CrisisService()


def _fallback_check(text: str) -> bool:
    """Mirror CrisisService.check() logic against the fallback list only."""
    keywords = service._FALLBACK_KEYWORDS
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(k.lower()) for k in keywords) + r")\b")
    return bool(pattern.search(text.lower()))


def test_detects_direct_crisis_phrase():
    assert _fallback_check("I want to kill myself") is True


def test_detects_self_harm_phrase():
    assert _fallback_check("I keep thinking about hurting myself") is True


def test_does_not_flag_unrelated_text():
    assert _fallback_check("I had a great day at work today") is False


def test_does_not_flag_partial_word_matches():
    # "class" contains no crisis substrings that should false-positive
    assert _fallback_check("My class today was about overdose prevention policy") is True
    assert _fallback_check("I am classifying my documents") is False


def test_helpline_message_contains_key_resources():
    from app.services.crisis_service import format_helplines_message
    message = format_helplines_message()
    assert "iCall" in message
    assert "AASRA" in message
