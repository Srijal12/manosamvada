"""
Manosamvada — Entry point.

Local development:
    python run.py

Production (recommended):
    gunicorn -w 4 -b 0.0.0.0:8000 run:app
"""

import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = app.config.get("DEBUG", False)
    app.run(host="0.0.0.0", port=port, debug=debug)
