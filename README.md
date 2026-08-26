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

## API Endpoints

- `GET /` - API info
- `GET /health` - Health check

## Project Structure

```
app/
├── api/          # API endpoints
├── models/       # Database models
├── services/     # Business logic
├── tasks/        # Celery tasks
├── llm/          # LLM client
└── core/         # Config, auth, database
```
