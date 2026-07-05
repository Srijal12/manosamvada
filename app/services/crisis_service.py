"""
Crisis Detection Service for Manosamvada.

Provides a database-driven crisis keyword checker that integrates
with the emotion detector as a secondary safety layer.
"""

from typing import Optional
from ..extensions import mysql
import re


CRISIS_HELPLINES = {
    "India": {
        "iCall": "9152987821",
        "Vandrevala Foundation": "1860-2662-345 (24/7)",
        "AASRA": "9820466627",
        "Snehi": "044-24640050",
    },
    "International": {
        "Crisis Text Line": "Text HOME to 741741",
        "International Association for Suicide Prevention": "https://www.iasp.info/resources/Crisis_Centres/",
    },
}


def format_helplines_message() -> str:
    """Format helpline information into a readable string."""
    lines = [
        "I hear you, and I'm here with you right now.",
        "",
        "Please reach out to one of these helplines — trained professionals are available to help:",
        "",
        "India:",
    ]
    for name, number in CRISIS_HELPLINES["India"].items():
        lines.append(f"  - {name}: {number}")

    lines += ["", "International:"]
    for name, info in CRISIS_HELPLINES["International"].items():
        lines.append(f"  - {name}: {info}")

    lines += [
        "",
        "You are not alone. Your life has value. Please talk to someone right now.",
    ]
    return "\n".join(lines)


class CrisisService:
    """
    Checks user messages against a database-driven list of crisis keywords.
    Falls back to an in-memory list if the database is unavailable.
    """

    _FALLBACK_KEYWORDS = [
        "suicide", "suicidal", "kill myself", "end my life", "want to die",
        "self harm", "self-harm", "cut myself", "hurt myself", "no reason to live",
        "better off dead", "cant go on", "give up on life", "overdose",
        "not worth living", "ending it all",
    ]

    def __init__(self):
        self._compiled_fallback: Optional[re.Pattern] = None

    def _get_db_keywords(self) -> list[str]:
        """Fetch crisis keywords from the database."""
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT keyword FROM crisis_keywords WHERE is_active = 1")
            rows = cur.fetchall()
            cur.close()
            return [row["keyword"] for row in rows] if rows else []
        except Exception:
            return []

    def check(self, text: str) -> bool:
        """
        Check if the given text contains any crisis keywords.

        Args:
            text: User message to check.

        Returns:
            True if crisis content detected, False otherwise.
        """
        if not text:
            return False

        keywords = self._get_db_keywords() or self._FALLBACK_KEYWORDS
        normalized = text.lower()

        pattern = re.compile(
            r"\b(?:" + "|".join(re.escape(k.lower()) for k in keywords) + r")\b"
        )
        return bool(pattern.search(normalized))

    def log_crisis_event(self, user_id: Optional[int], message: str) -> None:
        """
        Log a crisis detection event to the database for admin review.

        Args:
            user_id: ID of the logged-in user (None for guests).
            message: The message that triggered crisis detection.
        """
        try:
            cur = mysql.connection.cursor()
            cur.execute(
                """
                INSERT INTO crisis_logs (user_id, message_snippet, detected_at)
                VALUES (%s, %s, NOW())
                """,
                (user_id, message[:200]),
            )
            mysql.connection.commit()
            cur.close()
        except Exception:
            pass

    def get_helplines(self) -> dict:
        """Return helpline information."""
        return CRISIS_HELPLINES

    def get_helplines_message(self) -> str:
        """Return formatted helpline message."""
        return format_helplines_message()


crisis_service = CrisisService()
