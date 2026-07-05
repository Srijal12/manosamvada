"""
Analytics Service for Manosamvada.

Provides aggregate insights for user dashboards and the admin panel:
mood trends over time, session frequency, crisis event summaries,
and CSV export of a user's chat history.
"""

import csv
import io
from datetime import datetime, timedelta
from typing import Optional
from ..extensions import mysql


class AnalyticsService:
    """Aggregates chat and emotion data for dashboards and exports."""

    def get_user_mood_trend(self, user_id: int, days: int = 30) -> list[dict]:
        """
        Return daily dominant emotion counts for a user over the last N days.

        Returns:
            List of {date, emotion, count} dicts, ordered by date ascending.
        """
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT DATE(cm.created_at) AS day, cm.emotion_label AS emotion,
                   COUNT(*) AS count
            FROM chat_messages cm
            JOIN chat_sessions cs ON cm.session_id = cs.id
            WHERE cs.user_id = %s
              AND cm.role = 'user'
              AND cm.emotion_label IS NOT NULL
              AND cm.created_at >= %s
            GROUP BY day, emotion
            ORDER BY day ASC
            """,
            (user_id, datetime.utcnow() - timedelta(days=days)),
        )
        rows = cur.fetchall() or []
        cur.close()
        return [
            {"date": r["day"].isoformat(), "emotion": r["emotion"], "count": r["count"]}
            for r in rows
        ]

    def get_user_summary(self, user_id: int) -> dict:
        """Return summary stats for a user's dashboard."""
        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT COUNT(*) AS cnt FROM chat_sessions WHERE user_id = %s", (user_id,)
        )
        total_sessions = cur.fetchone()["cnt"]

        cur.execute(
            """
            SELECT COUNT(*) AS cnt FROM chat_messages cm
            JOIN chat_sessions cs ON cm.session_id = cs.id
            WHERE cs.user_id = %s AND cm.role = 'user'
            """,
            (user_id,),
        )
        total_messages = cur.fetchone()["cnt"]

        cur.execute(
            """
            SELECT cm.emotion_label AS emotion, COUNT(*) AS cnt
            FROM chat_messages cm
            JOIN chat_sessions cs ON cm.session_id = cs.id
            WHERE cs.user_id = %s AND cm.emotion_label IS NOT NULL
            GROUP BY cm.emotion_label
            ORDER BY cnt DESC
            LIMIT 1
            """,
            (user_id,),
        )
        top_emotion_row = cur.fetchone()
        top_emotion = top_emotion_row["emotion"] if top_emotion_row else "neutral"

        cur.close()
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "top_emotion": top_emotion,
        }

    def get_admin_overview(self) -> dict:
        """Return platform-wide stats for the admin dashboard."""
        cur = mysql.connection.cursor()

        cur.execute("SELECT COUNT(*) AS cnt FROM users")
        total_users = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM chat_sessions")
        total_sessions = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM chat_messages")
        total_messages = cur.fetchone()["cnt"]

        cur.execute(
            "SELECT COUNT(*) AS cnt FROM crisis_logs WHERE reviewed = 0"
        )
        pending_crisis = cur.fetchone()["cnt"]

        cur.execute(
            """
            SELECT emotion_label AS emotion, COUNT(*) AS cnt
            FROM chat_messages WHERE emotion_label IS NOT NULL
            GROUP BY emotion_label ORDER BY cnt DESC
            """
        )
        emotion_breakdown = cur.fetchall() or []

        cur.close()
        return {
            "total_users": total_users,
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "pending_crisis_reviews": pending_crisis,
            "emotion_breakdown": emotion_breakdown,
        }

    def export_user_history_csv(self, user_id: int) -> str:
        """
        Export a user's full chat history as CSV text.

        Returns:
            CSV-formatted string.
        """
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT cs.title AS session_title, cm.role, cm.content,
                   cm.emotion_label, cm.created_at
            FROM chat_messages cm
            JOIN chat_sessions cs ON cm.session_id = cs.id
            WHERE cs.user_id = %s
            ORDER BY cm.created_at ASC
            """,
            (user_id,),
        )
        rows = cur.fetchall() or []
        cur.close()

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Session", "Role", "Message", "Emotion", "Timestamp"])
        for r in rows:
            writer.writerow([
                r["session_title"],
                r["role"],
                r["content"],
                r["emotion_label"] or "",
                r["created_at"].isoformat() if r["created_at"] else "",
            ])
        return buffer.getvalue()


analytics_service = AnalyticsService()
