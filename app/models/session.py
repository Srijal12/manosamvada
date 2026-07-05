"""
Chat session data-access helpers for Manosamvada.
"""

from ..extensions import mysql
from typing import Optional


def get_session_by_id(session_id: int, user_id: int) -> Optional[dict]:
    """Fetch a chat session, scoped to its owning user."""
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT * FROM chat_sessions WHERE id = %s AND user_id = %s",
        (session_id, user_id),
    )
    row = cur.fetchone()
    cur.close()
    return row


def list_user_sessions(user_id: int, limit: int = 20) -> list[dict]:
    """List a user's chat sessions, most recent first, with message counts."""
    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT cs.id, cs.title, cs.created_at,
               (SELECT COUNT(*) FROM chat_messages WHERE session_id = cs.id) AS msg_count
        FROM chat_sessions cs
        WHERE cs.user_id = %s
        ORDER BY cs.created_at DESC LIMIT %s
        """,
        (user_id, limit),
    )
    rows = cur.fetchall() or []
    cur.close()
    return rows


def delete_session(session_id: int, user_id: int) -> bool:
    """Delete a session (and cascade its messages) if owned by the user."""
    cur = mysql.connection.cursor()
    cur.execute(
        "DELETE FROM chat_sessions WHERE id = %s AND user_id = %s",
        (session_id, user_id),
    )
    mysql.connection.commit()
    deleted = cur.rowcount > 0
    cur.close()
    return deleted
