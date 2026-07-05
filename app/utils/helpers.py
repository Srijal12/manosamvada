"""
General-purpose helper utilities for Manosamvada.
"""

from datetime import datetime


def format_timestamp(dt: datetime | None, fmt: str = "%b %d, %Y · %I:%M %p") -> str:
    """Format a datetime object for display, safely handling None."""
    if not dt:
        return ""
    return dt.strftime(fmt)


def truncate_text(text: str, max_length: int = 60) -> str:
    """Truncate text to a max length, appending an ellipsis if cut."""
    if not text:
        return ""
    return text if len(text) <= max_length else text[: max_length - 1].rstrip() + "…"


def emotion_to_emoji(emotion: str | None) -> str:
    """Map an emotion label to a representative emoji for UI display."""
    mapping = {
        "happy": "🙂",
        "sad": "😔",
        "angry": "😤",
        "anxious": "😟",
        "crisis": "💛",
        "neutral": "💭",
    }
    return mapping.get(emotion, "💭")


def paginate(items: list, page: int = 1, per_page: int = 20) -> dict:
    """Simple in-memory pagination helper."""
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": max(1, (total + per_page - 1) // per_page),
    }
