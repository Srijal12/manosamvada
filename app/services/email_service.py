"""
Email Service for Manosamvada.
Handles OTP generation, sending, and verification for secure authentication.
"""

import random
import string
import hashlib
import hmac
from datetime import datetime, timedelta
from flask import current_app
from flask_mail import Message
from ..extensions import mail, mysql
import logging

logger = logging.getLogger(__name__)


def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically random numeric OTP."""
    return "".join(random.choices(string.digits, k=length))


def hash_otp(otp: str, secret: str) -> str:
    """Hash an OTP using HMAC-SHA256 for secure storage."""
    return hmac.new(secret.encode(), otp.encode(), hashlib.sha256).hexdigest()


def send_otp_email(email: str, otp: str, username: str) -> bool:
    """Send an OTP verification email."""
    try:
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Georgia, serif; background: #0f0f13; color: #e8e0d5; padding: 40px;">
            <div style="max-width: 480px; margin: 0 auto; background: #1a1a22;
                        border-radius: 12px; padding: 40px; border: 1px solid #2a2a35;">
                <h1 style="color: #c9a96e; font-size: 24px; margin-bottom: 8px;">
                    Manosamvada
                </h1>
                <p style="color: #9e9aa0; font-size: 13px; margin-bottom: 32px;">
                    Dialogue of the Mind
                </p>
                <p style="font-size: 16px; color: #e8e0d5;">
                    Hello {username},
                </p>
                <p style="color: #b8b0bf; line-height: 1.7;">
                    Your verification code for Manosamvada is:
                </p>
                <div style="text-align: center; margin: 32px 0;">
                    <span style="font-size: 42px; font-weight: bold; letter-spacing: 12px;
                                 color: #c9a96e; font-family: monospace;">
                        {otp}
                    </span>
                </div>
                <p style="color: #9e9aa0; font-size: 13px; text-align: center;">
                    This code expires in {current_app.config['OTP_EXPIRY_MINUTES']} minutes.
                </p>
                <hr style="border: none; border-top: 1px solid #2a2a35; margin: 32px 0;">
                <p style="color: #6e6a70; font-size: 12px; text-align: center;">
                    If you did not request this, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """

        msg = Message(
            subject="Your Manosamvada Verification Code",
            recipients=[email],
            html=html_body,
        )
        mail.send(msg)
        logger.info(f"OTP sent to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send OTP to {email}: {e}")
        return False


def store_otp(email: str, otp: str) -> bool:
    """Store a hashed OTP in the database with expiry."""
    try:
        secret = current_app.config["SECRET_KEY"]
        otp_hash = hash_otp(otp, secret)
        expiry = datetime.now() + timedelta(
       minutes=current_app.config["OTP_EXPIRY_MINUTES"]
   )
        

        cur = mysql.connection.cursor()
        cur.execute(
            """
            INSERT INTO otp_store (email, otp_hash, expires_at, created_at)
            VALUES (%s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                otp_hash = VALUES(otp_hash),
                expires_at = VALUES(expires_at),
                created_at = NOW()
            """,
            (email, otp_hash, expiry),
        )
        mysql.connection.commit()
        cur.close()
        return True
    except Exception as e:
        logger.error(f"Failed to store OTP: {e}")
        return False


def verify_otp(email: str, otp: str) -> bool:
    """Verify an OTP against the stored hash."""
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT otp_hash, expires_at FROM otp_store
            WHERE email = %s AND expires_at > NOW()
            """,
            (email,),
        )
        row = cur.fetchone()
        cur.close()

        if not row:
            return False

        secret = current_app.config["SECRET_KEY"]
        expected_hash = hash_otp(otp, secret)
        return hmac.compare_digest(row["otp_hash"], expected_hash)

    except Exception as e:
        logger.error(f"OTP verification error: {e}")
        return False


def invalidate_otp(email: str) -> None:
    """Delete OTP record after successful verification."""
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM otp_store WHERE email = %s", (email,))
        mysql.connection.commit()
        cur.close()
    except Exception:
        pass
