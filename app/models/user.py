"""
User data-access helpers for Manosamvada.

The project uses raw parameterized SQL (via Flask-MySQLdb) rather than a
full ORM, so this module centralizes user-related queries in one place
for reuse across routes.
"""

from ..extensions import mysql
from typing import Optional


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Fetch a single user by primary key."""
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id, username, email, is_verified, is_admin, created_at, last_login "
        "FROM users WHERE id = %s",
        (user_id,),
    )
    row = cur.fetchone()
    cur.close()
    return row


def get_user_by_email(email: str) -> Optional[dict]:
    """Fetch a single user by email address."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    row = cur.fetchone()
    cur.close()
    return row


def list_all_users(limit: int = 100, offset: int = 0) -> list[dict]:
    """List users for the admin panel, most recent first."""
    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT id, username, email, is_verified, is_admin, created_at, last_login
        FROM users ORDER BY created_at DESC LIMIT %s OFFSET %s
        """,
        (limit, offset),
    )
    rows = cur.fetchall() or []
    cur.close()
    return rows
