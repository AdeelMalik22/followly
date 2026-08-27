# Followly Project Documentation

## Overview

Followly is an AI-powered sales follow-up agent for small businesses, starting with dental clinics. The system connects to WhatsApp, Instagram, email, and website chat to automatically qualify leads, book appointments, and follow up with prospects.

## Project Structure

```
followly/
├── app/
│   ├── api/              # FastAPI route handlers (thin controllers)
│   │   ├── auth.py       # Auth REST endpoints (/api/v1/auth/signup, /login)
│   │   ├── pages.py      # HTML page routes (/login, /signup)
│   │   ├── chat.py       # Demo chat widget (/chat)
│   │   ├── knowledge.py  # Knowledge base CRUD endpoints
│   │   ├── whatsapp.py   # WhatsApp webhook handler
│   │   ├── calendar.py   # Google Calendar OAuth
│   │   └── dependencies.py # Shared dependencies (auth, business context)
│   ├── models/           # SQLAlchemy database models
│   │   └── models.py     # Business, User, Lead, Conversation, Message, Appointment, etc.
│   ├── schemas/          # Pydantic validation schemas
│   │   ├── auth.py       # Auth request/response schemas
│   │   └── knowledge.py  # Knowledge base schemas
│   ├── services/         # Business logic layer
│   │   ├── auth_service.py       # User/business creation, authentication
│   │   └── knowledge_service.py  # Knowledge base CRUD operations
│   ├── tasks/            # Celery background tasks (future: follow-ups)
│   ├── llm/              # LLM integration layer
│   │   ├── config.py     # Provider configuration (OpenRouter/OpenAI/Anthropic)
│   │   └── client.py     # Chat wrapper with tool support
│   ├── templates/        # Jinja2 HTML templates
│   │   ├── login.html    # Login page (dark glassmorphic UI)
│   │   ├── signup.html   # Signup page (dark glassmorphic UI)
│   │   └── chat.html     # Demo chat widget
│   └── core/             # Core infrastructure
│       ├── config.py     # Settings and environment variables
│       ├── database.py   # SQLAlchemy setup and session management
│       └── security.py   # JWT auth and password hashing
├── scripts/              # CLI utilities
│   ├── test_agent.py     # Non-interactive agent testing
│   └── chat_agent.py     # Interactive chat CLI
├── alembic/              # Database migrations
├── tests/                # Test files (TODO)
├── .env                  # Environment variables (not committed)
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
├── plan.md               # Implementation roadmap
├── idea.md               # Product vision
└── DEV_NOTES.md          # Development guidelines
```

## Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Task Queue**: Celery + Redis (for follow-ups and async jobs)
- **LLM**: Swappable provider (OpenRouter/OpenAI/Anthropic) via OpenAI-compatible API
- **Auth**: JWT tokens with bcrypt password hashing
- **Frontend**: Next.js (planned, not yet implemented)

## Architecture Principles

### Multi-Tenant from Day One
Every table has a `business_id` foreign key. All queries filter by `business_id` to ensure data isolation between businesses.

### Service Layer Pattern
- **API Layer** (`app/api/`): Thin controllers handling HTTP requests/responses
- **Service Layer** (`app/services/`): Business logic, database operations, complex workflows
- **Models** (`app/models/`): Database schema definitions only

### Swappable LLM Provider
Configure via environment variables. No code changes needed to switch between OpenRouter (free models), OpenAI, or Anthropic:

```bash
LLM_PROVIDER=openrouter  # or openai, anthropic
OPENROUTER_API_KEY=sk-...
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

## Database Schema

### Core Tables
- **businesses**: Business accounts (clinics)
- **users**: User accounts with business_id FK
- **leads**: Customer leads with status tracking
- **conversations**: Chat threads per lead/channel
- **messages**: Individual messages in conversations
- **appointments**: Booked appointments with calendar integration
- **knowledge_base**: Business-specific FAQs, pricing, services
- **follow_up_rules**: Automated follow-up configuration (future)

### Lead Status Flow
```
NEW → CONTACTED → QUALIFIED → BOOKED
              ↓
            COLD → RECOVERED
              ↓
        NOT_INTERESTED
```

## Development Guidelines

### Git Workflow
- **DO NOT** add Claude as contributor in commits
- Push meaningful commits for each feature/API/bugfix
- Commit message format: Present tense, concise ("Add auth API" not "Added auth API")

### Token Efficiency
- Minimize verbose explanations
- Prioritize working code over commentary
- Brief status updates only
- Let code and commits speak for themselves

### Code Style
- Use type hints for function parameters and return values
- Keep functions focused and single-purpose
- Business logic goes in services, not API handlers
- Name variables/functions descriptively (no abbreviations unless obvious)

### Database Migrations
```bash
# Create migration after model changes
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing
```bash
# Test LLM connectivity and conversation flow
python scripts/test_agent.py

# Interactive chat with agent
python scripts/chat_agent.py

# Run API server for manual testing
uvicorn app.main:app --reload
```

## Current Implementation Status

### ✅ Completed
- [x] FastAPI project structure
- [x] Database models (all core tables)
- [x] PostgreSQL connection and migrations
- [x] JWT authentication (signup/login)
- [x] Knowledge base CRUD API
- [x] LLM layer with swappable providers
- [x] Service layer separation
- [x] CLI testing tools
- [x] Login page (`/login`) — dark glassmorphic UI, JWT stored in sessionStorage/localStorage
- [x] Signup page (`/signup`) — multi-field form with password strength indicator, inline validation

### 🚧 In Progress / Next Steps
- [ ] WhatsApp Cloud API integration (webhook + send)
- [ ] Conversation engine with tool calling
- [ ] Google Calendar integration (OAuth + booking)
- [ ] Follow-up engine (Celery tasks)
- [ ] Metrics/analytics API
- [ ] Next.js dashboard frontend

### 📋 Planned (Phase 2+)
- [ ] Instagram DMs integration
- [ ] Email integration (IMAP/SMTP)
- [ ] Website chat widget
- [ ] Stripe payment integration
- [ ] Lead status automation
- [ ] Cold lead reactivation

## API Usage Examples

### Signup
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dentist@example.com",
    "password": "password123",
    "business_name": "Bright Smiles Dental"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dentist@example.com",
    "password": "password123"
  }'
```

### Create Knowledge Base Entry (requires auth token)
```bash
curl -X POST http://localhost:8000/api/v1/knowledge \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "category": "services",
    "question": "How much is teeth cleaning?",
    "answer": "Regular teeth cleaning is $120 and takes 45 minutes."
  }'
```

## Environment Variables

Required variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://myuser:123@localhost:5432/followly
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# LLM Provider
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free

# WhatsApp (future)
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_ACCESS_TOKEN=

# Google Calendar (future)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/calendar/callback
```

## Common Issues & Solutions

### Migration Errors
- **"metadata is a reserved attribute"**: Column name conflicts with SQLAlchemy internals. Use `extra_data` instead.
- **Validation error for Settings**: Add missing env vars to `Settings` class in `app/core/config.py` or set `extra = "ignore"` in Config.

### LLM Connection Issues
- Verify API key is set correctly in `.env`
- Check provider name matches one of: `openrouter`, `openai`, `anthropic`
- Test with `python scripts/test_agent.py`

### Database Connection Issues
- Ensure PostgreSQL is running: `sudo systemctl status postgresql`
- Verify credentials in DATABASE_URL
- Create database if it doesn't exist: `createdb -U myuser followly`

## Contributing

This is a single-developer project with AI assistance. Follow the guidelines in `DEV_NOTES.md`:
- Keep commits atomic and meaningful
- No WIP commits on master
- Test before pushing
- Document complex logic inline

## Deployment (Future)

Target platforms:
- Backend: Render or Railway (free tier initially)
- Database: Managed PostgreSQL (Render/Railway/Supabase)
- Redis: Upstash or Render
- Frontend: Vercel

## References

- **Plan**: See `plan.md` for full 6-phase implementation roadmap
- **Product Vision**: See `idea.md` for market strategy and features
- **Dev Notes**: See `DEV_NOTES.md` for git and development conventions
