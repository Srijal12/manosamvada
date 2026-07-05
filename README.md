# Manosamvada — मनःसंवाद (Dialogue of the Mind)

Manosamvada is an empathetic AI mental health support chatbot. It listens for
emotional tone before it answers, adjusts how it responds based on what it
detects, and has a dedicated safety layer for crisis language.

> Manosamvada offers supportive conversation, not therapy or medical advice.
> It is not a substitute for professional mental health care.

## Features

- **Secure accounts** — registration with OTP email verification, bcrypt-hashed
  passwords, rate-limited login/registration endpoints.
- **Two-layer response pipeline** — a rule-based emotion detector classifies
  each message (happy, sad, angry, anxious, neutral, crisis) and injects a
  tone directive into the prompt sent to Meta-Llama-3.1-8B-Instruct via the
  SambaNova API.
- **Crisis detection** — messages are checked against a database-driven
  keyword list; detected crisis messages trigger an immediate supportive
  response with helpline information, and are logged for admin review.
- **Persistent chat history** — conversations are saved per user, with
  AI-generated session titles, full history retrieval, and search.
- **Analytics dashboards** — a user-facing mood-trend view and CSV export,
  plus an admin dashboard with platform stats and crisis-log review.
- **Guest mode** — anyone can try the chatbot without creating an account
  (guest conversations are not persisted).

## Tech Stack

| Layer      | Technology |
|------------|------------|
| Backend    | Python, Flask (application factory + blueprints) |
| Database   | MySQL (3NF schema, raw parameterized SQL) |
| AI         | SambaNova API (Meta-Llama-3.1-8B-Instruct) via the OpenAI SDK |
| Frontend   | Jinja2 templates, vanilla JavaScript, hand-written CSS |
| Auth       | bcrypt password hashing, HMAC-SHA256 OTP hashing, Flask sessions |

## Project Structure

```
manosamvada/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Environment-based configuration
│   ├── extensions.py        # Flask extension instances
│   ├── models/               # Data-access helpers (raw SQL, no ORM)
│   ├── routes/                # Blueprints: auth, chat, dashboard, admin
│   ├── services/               # Emotion detection, AI, crisis, email, analytics
│   ├── utils/                   # Security helpers, formatting helpers
│   └── static/                   # CSS, JS
├── templates/                # Jinja2 templates
├── database/
│   ├── schema.sql            # Full 3NF schema
│   └── seed_data.sql         # Crisis keywords + response templates
├── tests/                    # pytest unit tests (no DB required)
├── run.py                    # Local dev entry point
└── requirements.txt
```

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/<your-username>/manosamvada.git
cd manosamvada
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Fill in `.env` with your own values — **never commit this file**. You will need:

- A MySQL connection (`MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`)
- A [SambaNova API key](https://cloud.sambanova.ai/) (`SAMBANOVA_API_KEY`)
- SMTP credentials for OTP email delivery (a Gmail App Password works well)

### 3. Create the database

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed_data.sql
```

`seed_data.sql` ships with crisis keywords and response templates, plus a
placeholder admin row. Before running it, generate your own admin password
hash and replace the placeholder in the file:

```bash
python -c "import bcrypt; print(bcrypt.hashpw(b'YourOwnPassword1!', bcrypt.gensalt()).decode())"
```

### 4. Run the app

```bash
python run.py
```

Visit `http://localhost:5000`.

### 5. Run tests

```bash
pytest tests/ -v
```

The included tests cover emotion detection, crisis keyword matching, and
password/input security utilities — none require a live database connection.

## Deployment notes

- Set `FLASK_ENV=production` and `SESSION_COOKIE_SECURE=True` behind HTTPS.
- Run with a production WSGI server: `gunicorn -w 4 -b 0.0.0.0:8000 run:app`.
- Rotate `SECRET_KEY` and all API keys before going live; none of the values
  in `.env.example` are usable credentials.

## Known limitations & roadmap

- Emotion detection is currently rule-based (keyword/regex matching), so it
  can miss sarcasm or indirectly expressed emotion.
- **Planned:** replace/augment the detector with a fine-tuned transformer
  model (e.g., BERT) trained on mental-health conversation data for more
  nuanced emotion understanding.

## License

MIT — see `LICENSE` for details. This project is provided for educational
and portfolio purposes; if adapting it for real users, have the crisis-safety
flow reviewed by a mental health professional first.
