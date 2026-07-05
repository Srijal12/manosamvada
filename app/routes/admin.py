"""
Admin routes for Manosamvada.
Provides platform-wide analytics and crisis-log review for administrators.
"""

from flask import Blueprint, render_template, jsonify, request
from ..utils.security import admin_required
from ..services.analytics_service import analytics_service
from ..models.user import list_all_users
from ..models.crisis import list_crisis_logs, mark_reviewed
from flask import session

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@admin_required
def admin_dashboard():
    overview = analytics_service.get_admin_overview()
    users = list_all_users(limit=50)
    crisis_logs = list_crisis_logs(reviewed=False, limit=25)

    return render_template(
        "admin/admin_dashboard.html",
        overview=overview,
        users=users,
        crisis_logs=crisis_logs,
    )


@admin_bp.route("/crisis-logs")
@admin_required
def crisis_logs_api():
    """Return crisis logs, optionally filtered by review status."""
    reviewed_param = request.args.get("reviewed")
    reviewed = None
    if reviewed_param is not None:
        reviewed = reviewed_param == "1"

    logs = list_crisis_logs(reviewed=reviewed)
    return jsonify({
        "logs": [
            {
                "id": log["id"],
                "user_id": log["user_id"],
                "username": log.get("username"),
                "email": log.get("email"),
                "message_snippet": log["message_snippet"],
                "detected_at": log["detected_at"].isoformat() if log["detected_at"] else None,
                "reviewed": bool(log["reviewed"]),
            }
            for log in logs
        ]
    })


@admin_bp.route("/crisis-logs/<int:log_id>/review", methods=["POST"])
@admin_required
def review_crisis_log(log_id: int):
    """Mark a crisis log as reviewed by the current admin."""
    reviewer_id = session.get("user_id")
    mark_reviewed(log_id, reviewer_id)
    return jsonify({"success": True})
