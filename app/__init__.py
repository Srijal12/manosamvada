"""
Application factory for Manosamvada.
Uses the factory pattern for flexible instantiation across environments.
"""

from flask import Flask
from .config import get_config
from .extensions import mysql, mail, limiter


def create_app(config_class=None):
    """
    Create and configure the Flask application.

    Args:
        config_class: Optional config override (useful for testing).

    Returns:
        Configured Flask application instance.
    """
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="static",
    )

    cfg = config_class or get_config()
    app.config.from_object(cfg)

    mysql.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    from .routes.auth import auth_bp
    from .routes.chat import chat_bp
    from .routes.dashboard import dashboard_bp
    from .routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    from flask import render_template, redirect, url_for, session

    @app.route("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("chat.chat_page"))
        return render_template("index.html")

    @app.route("/guest")
    def guest():
        session["guest_mode"] = True
        session["user_id"] = None
        session["username"] = "Guest"
        return redirect(url_for("chat.chat_page"))

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        from flask import jsonify
        return jsonify({"error": "Rate limit exceeded. Please slow down."}), 429

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app
