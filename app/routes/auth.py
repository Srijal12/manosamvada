"""
Authentication routes for Manosamvada.
Handles: Register, Login, OTP Verification, Logout.
All passwords are bcrypt-hashed. Email verification uses HMAC-secured OTPs.
"""

from flask import (
    Blueprint, request, render_template, redirect,
    url_for, session, flash, jsonify,
)
from ..extensions import mysql, limiter
from ..utils.security import (
    hash_password, verify_password, validate_password_strength,
    sanitize_input, validate_email,
)
from ..services.email_service import (
    generate_otp, send_otp_email, store_otp,
    verify_otp, invalidate_otp,
)
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if session.get("user_id"):
        return redirect(url_for("chat.chat_page"))

    if request.method == "POST":
        username = sanitize_input(request.form.get("username", ""), 50)
        email = sanitize_input(request.form.get("email", ""), 254).lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not all([username, email, password, confirm]):
            flash("All fields are required.", "error")
            return render_template("auth/register.html")

        if not validate_email(email):
            flash("Please enter a valid email address.", "error")
            return render_template("auth/register.html")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("auth/register.html")

        is_strong, msg = validate_password_strength(password)
        if not is_strong:
            flash(msg, "error")
            return render_template("auth/register.html")

        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT id FROM users WHERE email = %s OR username = %s",
            (email, username),
        )
        if cur.fetchone():
            cur.close()
            flash("An account with this email or username already exists.", "error")
            return render_template("auth/register.html")
        cur.close()

        session["pending_registration"] = {
            "username": username,
            "email": email,
            "password_hash": hash_password(password),
        }

        otp = generate_otp()
        if not store_otp(email, otp):
            flash("Failed to generate verification code. Please try again.", "error")
            return render_template("auth/register.html")

        if not send_otp_email(email, otp, username):
            flash("Failed to send verification email. Please check your email address.", "error")
            return render_template("auth/register.html")

        session["otp_email"] = email
        flash(f"Verification code sent to {email}", "success")
        return redirect(url_for("auth.verify_otp_page"))

    return render_template("auth/register.html")


@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp_page():
    if not session.get("otp_email"):
        return redirect(url_for("auth.register"))

    if request.method == "POST":
        otp_input = request.form.get("otp", "").strip()
        email = session.get("otp_email")

        if not verify_otp(email, otp_input):
            flash("Invalid or expired verification code.", "error")
            return render_template("auth/verify_otp.html", email=email)

        pending = session.pop("pending_registration", None)
        if not pending:
            flash("Session expired. Please register again.", "error")
            return redirect(url_for("auth.register"))

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                """
                INSERT INTO users (username, email, password_hash, is_verified, created_at)
                VALUES (%s, %s, %s, 1, NOW())
                """,
                (pending["username"], email, pending["password_hash"]),
            )
            mysql.connection.commit()
            user_id = cur.lastrowid
            cur.close()

            invalidate_otp(email)
            session.pop("otp_email", None)

            session["user_id"] = user_id
            session["username"] = pending["username"]
            session["email"] = email
            session.permanent = True

            logger.info(f"New user registered: {email}")
            flash(f"Welcome to Manosamvada, {pending['username']}!", "success")
            return redirect(url_for("chat.chat_page"))

        except Exception as e:
            logger.error(f"Registration DB error: {e}")
            flash("An error occurred. Please try again.", "error")
            return render_template("auth/verify_otp.html", email=email)

    return render_template("auth/verify_otp.html", email=session.get("otp_email"))


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def login():
    if session.get("user_id"):
        return redirect(url_for("chat.chat_page"))

    if request.method == "POST":
        email = sanitize_input(request.form.get("email", ""), 254).lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter your email and password.", "error")
            return render_template("auth/login.html")

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                """
                SELECT id, username, email, password_hash, is_verified, is_admin
                FROM users WHERE email = %s
                """,
                (email,),
            )
            user = cur.fetchone()
            cur.close()

            if not user or not verify_password(password, user["password_hash"]):
                flash("Invalid email or password.", "error")
                return render_template("auth/login.html")

            if not user["is_verified"]:
                flash("Please verify your email before logging in.", "warning")
                return render_template("auth/login.html")

            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["email"] = user["email"]
            session["is_admin"] = bool(user["is_admin"])
            session.permanent = True

            cur = mysql.connection.cursor()
            cur.execute(
                "UPDATE users SET last_login = NOW() WHERE id = %s", (user["id"],)
            )
            mysql.connection.commit()
            cur.close()

            logger.info(f"User logged in: {email}")
            return redirect(url_for("chat.chat_page"))

        except Exception as e:
            logger.error(f"Login error: {e}")
            flash("An error occurred. Please try again.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    username = session.get("username", "User")
    session.clear()
    flash(f"Goodbye, {username}. Take care of yourself.", "info")
    return redirect(url_for("index"))
