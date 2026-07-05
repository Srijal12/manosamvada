"""
Unit tests for authentication security utilities.
These tests do not require a database connection.
Run with: pytest tests/test_auth.py -v
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils.security import (
    hash_password, verify_password, validate_password_strength,
    validate_email, sanitize_input,
)


def test_password_hash_and_verify_roundtrip():
    plain = "SecurePass1!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPass1!", hashed) is False


def test_password_strength_rejects_short_password():
    is_valid, _ = validate_password_strength("Sh0rt!")
    assert is_valid is False


def test_password_strength_rejects_missing_special_char():
    is_valid, _ = validate_password_strength("NoSpecial1")
    assert is_valid is False


def test_password_strength_accepts_strong_password():
    is_valid, _ = validate_password_strength("StrongPass1!")
    assert is_valid is True


def test_validate_email_accepts_valid_address():
    assert validate_email("user@example.com") is True


def test_validate_email_rejects_invalid_address():
    assert validate_email("not-an-email") is False
    assert validate_email("missing@domain") is False


def test_sanitize_input_escapes_html():
    result = sanitize_input("<script>alert(1)</script>")
    assert "<script>" not in result


def test_sanitize_input_truncates_long_text():
    long_text = "a" * 5000
    result = sanitize_input(long_text, max_length=100)
    assert len(result) <= 100
