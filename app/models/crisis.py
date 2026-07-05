"""
Crisis log data-access helpers for Manosamvada, used by the admin panel.
"""

from ..extensions import mysql


def list_crisis_logs(reviewed: bool | None = None, limit: int = 100) -> list[dict]:
    """List crisis event logs, optionally filtered by review status."""
    cur = mysql.connection.cursor()
    if reviewed is None:
        cur.execute(
            """
            SELECT cl.*, u.username, u.email FROM crisis_logs cl
            LEFT JOIN users u ON cl.user_id = u.id
            ORDER BY cl.detected_at DESC LIMIT %s
            """,
            (limit,),
        )
    else:
        cur.execute(
            """
            SELECT cl.*, u.username, u.email FROM crisis_logs cl
            LEFT JOIN users u ON cl.user_id = u.id
            WHERE cl.reviewed = %s
            ORDER BY cl.detected_at DESC LIMIT %s
            """,
            (int(reviewed), limit),
        )
    rows = cur.fetchall() or []
    cur.close()
    return rows


def mark_reviewed(log_id: int, reviewer_id: int) -> None:
    """Mark a crisis log entry as reviewed by an admin."""
    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE crisis_logs SET reviewed = 1, reviewed_by = %s WHERE id = %s",
        (reviewer_id, log_id),
    )
    mysql.connection.commit()
    cur.close()
