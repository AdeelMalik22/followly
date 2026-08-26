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
- `POST /api/v1/auth/signup` - Create account
- `POST /api/v1/auth/login` - Login

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
├── api/          # API endpoints
├── models/       # Database models
├── schemas/      # Pydantic schemas
├── services/     # Business logic
├── tasks/        # Celery tasks
├── llm/          # LLM client
└── core/         # Config, auth, database
scripts/          # CLI tools
```
