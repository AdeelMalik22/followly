# Followly Backend

AI Sales Follow-Up Agent API

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Setup environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run migrations:
```bash
alembic upgrade head
```

5. Start server:
```bash
uvicorn app.main:app --reload --port 8000
```

## Web UI

The server serves built-in HTML pages for authentication and the demo chat widget.

| Route | Description |
|-------|-------------|
| `GET /login` | Login page — authenticates via `/api/v1/auth/login`, stores JWT in sessionStorage/localStorage |
| `GET /signup` | Signup page — registers via `/api/v1/auth/signup`, stores JWT in sessionStorage |
| `GET /chat` | Demo chat widget (requires a seeded business) |

Both auth pages perform client-side validation, display inline field errors and toast notifications, and redirect to `/chat` on success.

## Testing the Agent

### Quick Test (Non-interactive)
```bash
python scripts/test_agent.py
```
Tests basic LLM connectivity, conversation flow, and tool calling.

### Interactive Chat
```bash
python scripts/chat_agent.py
```
Interactive CLI to chat with the agent. Commands:
- `/exit` - Exit chat
- `/reset` - Reset conversation
- `/help` - Show help

## API Endpoints

### Auth
- `POST /api/v1/auth/signup` — Create account (`email`, `owner_name`, `password`, `confirm_password`, `business_name`, `industry`, `terms_accepted`)
- `POST /api/v1/auth/login` — Login (`email`, `password`) → returns `access_token`

### Knowledge Base
- `POST /api/v1/knowledge` - Create entry
- `GET /api/v1/knowledge` - List entries
- `GET /api/v1/knowledge/{id}` - Get entry
- `PUT /api/v1/knowledge/{id}` - Update entry
- `DELETE /api/v1/knowledge/{id}` - Delete entry

### Health
- `GET /` - API info
- `GET /health` - Health check

## Project Structure

```
app/
├── api/
│   ├── auth.py         # Auth REST endpoints (/api/v1/auth/*)
│   ├── pages.py        # HTML page routes (/login, /signup)
│   ├── chat.py         # Demo chat widget (/chat)
│   ├── knowledge.py    # Knowledge base CRUD
│   ├── whatsapp.py     # WhatsApp webhook
│   ├── calendar.py     # Google Calendar OAuth
│   └── dependencies.py
├── models/             # SQLAlchemy models
├── schemas/            # Pydantic schemas
├── services/           # Business logic
├── tasks/              # Celery tasks
├── llm/                # LLM client
├── templates/
│   ├── login.html      # Login page
│   ├── signup.html     # Signup page
│   └── chat.html       # Demo chat widget
└── core/               # Config, security, database
scripts/                # CLI tools
```
