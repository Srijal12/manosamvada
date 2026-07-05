"""
Flask extension instances — initialized here, registered in app factory.
Avoids circular imports by separating instantiation from app binding.
"""

from flask_mysqldb import MySQL
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

mysql = MySQL()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)
