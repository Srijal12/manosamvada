"""
Chat routes for Manosamvada.
Handles: Chat page, message sending, session management, history retrieval.
"""

from flask import (
    Blueprint, request, jsonify, render_template,
    session, redirect, url_for,
)
from ..extensions import mysql, limiter
from ..utils.security import login_required, sanitize_input, get_current_user_id
from ..services.emotion_detector import emotion_detector
from ..services.ai_service import ai_service
from ..services.crisis_service import crisis_service
import logging

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)


def get_or_create_session(user_id: int) -> int:
    """Get the current active chat session or create a new one."""
    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT id FROM chat_sessions
        WHERE user_id = %s AND is_active = 1
        ORDER BY created_at DESC LIMIT 1
        """,
        (user_id,),
    )
    existing = cur.fetchone()

    if existing:
        cur.close()
        return existing["id"]

    cur.execute(
        """
        INSERT INTO chat_sessions (user_id, title, is_active, created_at)
        VALUES (%s, 'New Conversation', 1, NOW())
        """,
        (user_id,),
    )
    mysql.connection.commit()
    new_id = cur.lastrowid
    cur.close()
    return new_id


@chat_bp.route("/")
@login_required
def chat_page():
    user_id = get_current_user_id()
    username = session.get("username", "Friend")

    sessions_list = []
    if user_id:
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT id, title, created_at,
                   (SELECT COUNT(*) FROM chat_messages WHERE session_id = chat_sessions.id) AS msg_count
            FROM chat_sessions
            WHERE user_id = %s
            ORDER BY created_at DESC LIMIT 20
            """,
            (user_id,),
        )
        sessions_list = cur.fetchall() or []
        cur.close()

    return render_template(
        "chat/chat.html",
        username=username,
        sessions=sessions_list,
        is_guest=session.get("guest_mode", False),
    )


@chat_bp.route("/send", methods=["POST"])
@login_required
@limiter.limit("60 per minute")
def send_message():
    """
    Process a user message and return an AI response.

    Request JSON:
        { "message": str, "session_id": int | null }
    Response JSON:
        { "response": str, "emotion": str, "is_crisis": bool, "session_id": int }
    """
    data = request.get_json()
    if not data or not data.get("message"):
        return jsonify({"error": "Message is required"}), 400

    raw_message = data.get("message", "")
    user_message = sanitize_input(raw_message, max_length=2000)

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    user_id = get_current_user_id()
    is_guest = session.get("guest_mode", False)

    emotion_result = emotion_detector.detect(user_message)

    is_crisis = emotion_result.is_crisis or crisis_service.check(user_message)

    if is_crisis and user_id:
        crisis_service.log_crisis_event(user_id, user_message)

    chat_session_id = data.get("session_id")

    if user_id and not is_guest:
        if not chat_session_id:
            chat_session_id = get_or_create_session(user_id)

        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT role, content FROM chat_messages
            WHERE session_id = %s ORDER BY created_at ASC LIMIT 20
            """,
            (chat_session_id,),
        )
        history_rows = cur.fetchall() or []
        history = [{"role": r["role"], "content": r["content"]} for r in history_rows]
        cur.close()
    else:
        history = []

    ai_response = ai_service.generate_response(
        user_message=user_message,
        emotion_result=emotion_result,
        history=history,
    )

    if is_crisis:
        ai_response += "\n\n---\n" + crisis_service.get_helplines_message()

    if user_id and not is_guest and chat_session_id:
        try:
            cur = mysql.connection.cursor()

            cur.execute(
                """
                INSERT INTO chat_messages
                    (session_id, role, content, emotion_label, emotion_intensity, created_at)
                VALUES (%s, 'user', %s, %s, %s, NOW())
                """,
                (chat_session_id, user_message, emotion_result.label, emotion_result.intensity),
            )

            cur.execute(
                """
                INSERT INTO chat_messages
                    (session_id, role, content, emotion_label, emotion_intensity, created_at)
                VALUES (%s, 'assistant', %s, NULL, NULL, NOW())
                """,
                (chat_session_id, ai_response),
            )

            cur.execute(
                "SELECT COUNT(*) AS cnt FROM chat_messages WHERE session_id = %s",
                (chat_session_id,),
            )
            count = cur.fetchone()["cnt"]

            if count == 2:
                title = ai_service.generate_session_title(user_message)
                cur.execute(
                    "UPDATE chat_sessions SET title = %s WHERE id = %s",
                    (title, chat_session_id),
                )

            mysql.connection.commit()
            cur.close()

        except Exception as e:
            logger.error(f"Chat DB error: {e}")

    return jsonify({
        "response": ai_response,
        "emotion": emotion_result.label,
        "emotion_intensity": emotion_result.intensity,
        "is_crisis": is_crisis,
        "session_id": chat_session_id,
    })


@chat_bp.route("/history/<int:session_id>")
@login_required
def get_history(session_id: int):
    """Retrieve full chat history for a specific session."""
    user_id = get_current_user_id()

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id, title FROM chat_sessions WHERE id = %s AND user_id = %s",
        (session_id, user_id),
    )
    session_row = cur.fetchone()

    if not session_row:
        cur.close()
        return jsonify({"error": "Session not found"}), 404

    cur.execute(
        """
        SELECT role, content, emotion_label, created_at
        FROM chat_messages WHERE session_id = %s ORDER BY created_at ASC
        """,
        (session_id,),
    )
    messages = cur.fetchall() or []
    cur.close()

    return jsonify({
        "session_id": session_id,
        "title": session_row["title"],
        "messages": [
            {
                "role": m["role"],
                "content": m["content"],
                "emotion": m["emotion_label"],
                "timestamp": m["created_at"].isoformat() if m["created_at"] else None,
            }
            for m in messages
        ],
    })


@chat_bp.route("/new-session", methods=["POST"])
@login_required
def new_session():
    """Create a new chat session."""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE chat_sessions SET is_active = 0 WHERE user_id = %s AND is_active = 1",
            (user_id,),
        )
        cur.execute(
            """
            INSERT INTO chat_sessions (user_id, title, is_active, created_at)
            VALUES (%s, 'New Conversation', 1, NOW())
            """,
            (user_id,),
        )
        mysql.connection.commit()
        new_id = cur.lastrowid
        cur.close()
        return jsonify({"session_id": new_id})
    except Exception as e:
        logger.error(f"New session error: {e}")
        return jsonify({"error": "Could not create session"}), 500


@chat_bp.route("/delete-session/<int:session_id>", methods=["DELETE"])
@login_required
def delete_session_route(session_id: int):
    """Delete a chat session owned by the current user."""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    from ..models.session import delete_session
    deleted = delete_session(session_id, user_id)
    if not deleted:
        return jsonify({"error": "Session not found"}), 404
    return jsonify({"success": True})
