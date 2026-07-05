"""
Security utilities for Manosamvada.
Handles password hashing, input sanitization, and session management.
"""

import bcrypt
import re
import html
from functools import wraps
from flask import session, redirect, url_for, jsonify, request
from typing import Optional


def hash_password(plain_password: str) -> str:
    """Hash a password using bcrypt with a secure work factor."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed.encode("utf-8"))


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets minimum security requirements.

    Rules:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, "Password is strong."


def sanitize_input(text: str, max_length: int = 2000) -> str:
    """Sanitize user input to prevent XSS and injection attacks."""
    if not text:
        return ""
    text = text[:max_length]
    text = html.escape(text, quote=True)
    text = text.replace("\x00", "")
    return text.strip()


def validate_email(email: str) -> bool:
    """Validate email format using regex."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def login_required(f):
    """Decorator: Require authenticated session. Redirects unauthenticated requests."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id") and not session.get("guest_mode"):
            if request.is_json:
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator: Require admin role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            if request.is_json:
                return jsonify({"error": "Admin access required"}), 403
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def get_current_user_id() -> Optional[int]:
    """Return current user's ID from session, or None."""
    return session.get("user_id")
