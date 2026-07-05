"""
User dashboard routes for Manosamvada.
Provides mood analytics, session history, search, and CSV export.
"""

from flask import Blueprint, render_template, jsonify, request, Response, session
from ..utils.security import login_required, get_current_user_id
from ..services.analytics_service import analytics_service
from ..extensions import mysql

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def dashboard_home():
    user_id = get_current_user_id()
    if not user_id:
        # Guests don't have persisted analytics
        return render_template(
            "dashboard/dashboard.html",
            summary=None,
            mood_trend=[],
            username=session.get("username", "Friend"),
        )

    summary = analytics_service.get_user_summary(user_id)
    mood_trend = analytics_service.get_user_mood_trend(user_id)

    return render_template(
        "dashboard/dashboard.html",
        summary=summary,
        mood_trend=mood_trend,
        username=session.get("username", "Friend"),
    )


@dashboard_bp.route("/search")
@login_required
def search_sessions():
    """Search a user's chat sessions and messages by keyword."""
    user_id = get_current_user_id()
    query = request.args.get("q", "").strip()

    if not user_id or not query:
        return jsonify({"results": []})

    cur = mysql.connection.cursor()
    like_query = f"%{query}%"
    cur.execute(
        """
        SELECT DISTINCT cs.id, cs.title, cs.created_at
        FROM chat_sessions cs
        JOIN chat_messages cm ON cm.session_id = cs.id
        WHERE cs.user_id = %s AND (cs.title LIKE %s OR cm.content LIKE %s)
        ORDER BY cs.created_at DESC LIMIT 30
        """,
        (user_id, like_query, like_query),
    )
    rows = cur.fetchall() or []
    cur.close()

    return jsonify({
        "results": [
            {
                "id": r["id"],
                "title": r["title"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]
    })


@dashboard_bp.route("/export-csv")
@login_required
def export_csv():
    """Export the current user's full chat history as a downloadable CSV."""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Guests cannot export history"}), 403

    csv_data = analytics_service.export_user_history_csv(user_id)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=manosamvada_history.csv"},
    )
