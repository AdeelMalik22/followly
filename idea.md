# AI Sales Follow-Up Agent for Small Businesses

*Product & technical plan — dental clinic niche launch*

## 1. Product Idea

An AI agent connects to a business's WhatsApp, Instagram, email, and website chat. It talks to incoming leads, answers pricing and service questions, qualifies them, books appointments against a live calendar, and automatically follows up with leads who go quiet — including reactivating old/cold leads. The pitch to the business owner is simple: more leads converted into booked appointments, without touching "AI" as a selling point.

### Niche-first launch

Launch for one vertical first — **dental clinics** — before expanding to salons, real estate, auto dealerships, gyms, med spas, home-service companies, and lawyers.

### Core capabilities

- Answer pricing questions and explain services
- Qualify patients
- Book, reschedule, and cancel appointments
- Send reminders
- Follow up with leads automatically
- Reactivate old/cold leads
- Hand conversations off to staff when necessary

### Differentiator: an autonomous revenue agent, not a chatbot

Lead comes in → AI responds → qualifies → follows up → books → reminds → updates CRM → recovers missed/no-show customers. The dashboard should show concrete numbers, e.g. leads contacted, leads qualified, appointments booked, leads recovered, and estimated revenue — that's a far stronger pitch than "our AI can answer questions."

### Pricing (to test)

| Tier | Price | Includes |
|---|---|---|
| Starter | $49/mo | 1 AI agent + 1 channel |
| Growth | $149/mo | Multiple channels + calendar + CRM + automated follow-ups |
| Pro | $299/mo | Multiple agents + analytics + advanced workflows + higher usage |

*A one-time setup fee is also worth testing.*

## 2. Recommended Stack

**Backend:** Python + FastAPI, PostgreSQL, Celery + Redis, OpenRouter (swappable LLM layer).
**Frontend:** Next.js (React).

| Layer | Choice | Why |
|---|---|---|
| API/backend | FastAPI | Async-native, handles concurrent webhook + LLM + calendar calls cleanly; matches existing experience |
| Database | PostgreSQL | Stores conversations, leads, appointments; already familiar |
| Task queue | Celery + Redis (or APScheduler for MVP) | Follow-up scheduling, reminders, retries |
| Agent orchestration | LangChain or a thin custom tool-calling loop | Check calendar, book, update CRM, escalate to human |
| Channels | WhatsApp Cloud API (Meta), Instagram Graph API, IMAP/Gmail, website widget | Start with WhatsApp + website only |
| LLM | OpenRouter (free models now, swappable later) | Dynamic provider/model/key selection from env |
| Frontend/dashboard | Next.js | One codebase for marketing site + dashboard; prior experience with Next.js |
| Deploy | Render/Railway free tier to start | Low-cost infra until there are paying customers |

## 3. Backend Plan (build first)

### Foundation

- Project structure: `app/{api, models, services, tasks, llm, core}`
- Auth: business owner accounts (JWT), **multi-tenant from day one** — every table gets a `business_id` FK, even with a single pilot client
- DB models: `Business`, `User`, `Lead`, `Conversation`, `Message`, `Appointment`, `KnowledgeBaseEntry`, `FollowUpRule`

### Knowledge base

- Simple CRUD API + table for services/pricing/FAQs per business
- No vector DB at first — inject relevant rows directly into the system prompt; add embeddings/RAG only once content outgrows the context window

### Conversation engine

- Webhook endpoint for WhatsApp Cloud API — inbound message handler
- Core agent loop: load conversation history + knowledge base + lead state → call LLM with tools → execute tool calls → send reply
- Tools: `check_availability`, `book_appointment`, `reschedule_appointment`, `cancel_appointment`, `escalate_to_human`
- Google Calendar integration for availability/booking

### Follow-up engine

- Celery beat task scanning for stale conversations (no reply after a configurable delay)
- Follow-up message generation and send
- Lead status machine: `new → contacted → qualified → booked / cold → recovered`

### Dashboard API

- Aggregation endpoints: leads contacted, qualified, booked, recovered, estimated revenue (sum of booked appointment values)
- Business settings endpoints: knowledge base editor, follow-up cadence, calendar connection

### Ops

- Structured logging per conversation — needed to debug prompt/tool issues
- Rate limiting on inbound webhooks (reuse the existing `requestguard` library)
- Fallback model list in the LLM layer for when free OpenRouter models rate-limit or error

> Build and test each module via Postman/curl before touching the frontend — the whole system should be drivable via API alone first.

### Dynamic LLM provider/model/key selection from env

```python
# llm/config.py
import os
from dataclasses import dataclass

@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: str
    base_url: str | None = None

PROVIDER_DEFAULTS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "model_env": "OPENROUTER_MODEL",
        "default_model": "meta-llama/llama-3.1-8b-instruct:free",
    },
    "openai": {
        "base_url": None,
        "key_env": "OPENAI_API_KEY",
        "model_env": "OPENAI_MODEL",
        "default_model": "gpt-4o-mini",
    },
    "anthropic": {
        "base_url": None,
        "key_env": "ANTHROPIC_API_KEY",
        "model_env": "ANTHROPIC_MODEL",
        "default_model": "claude-sonnet-4-5",
    },
}

def load_llm_config() -> LLMConfig:
    provider = os.environ.get("LLM_PROVIDER", "openrouter").lower()
    if provider not in PROVIDER_DEFAULTS:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")

    cfg = PROVIDER_DEFAULTS[provider]
    api_key = os.environ.get(cfg["key_env"])
    if not api_key:
        raise RuntimeError(f"Missing {cfg['key_env']} in environment")

    model = os.environ.get(cfg["model_env"], cfg["default_model"])
    return LLMConfig(provider=provider, model=model, api_key=api_key, base_url=cfg["base_url"])
```

```python
# llm/client.py
from openai import OpenAI  # OpenRouter, OpenAI, and many providers share this API shape
from .config import load_llm_config

_client_cache = {}

def get_llm_client():
    cfg = load_llm_config()
    key = (cfg.provider, cfg.model)
    if key not in _client_cache:
        _client_cache[key] = (
            OpenAI(api_key=cfg.api_key, base_url=cfg.base_url) if cfg.base_url
            else OpenAI(api_key=cfg.api_key),
            cfg.model,
        )
    return _client_cache[key]

def chat(messages: list[dict], **kwargs):
    client, model = get_llm_client()
    return client.chat.completions.create(model=model, messages=messages, **kwargs)
```

```bash
# .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-xxxx
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

Switching providers later (e.g. to Anthropic) is just changing `LLM_PROVIDER` and setting the matching key — no code changes. Add a fallback model list before relying on this in front of paying customers, since free OpenRouter models have low rate limits and can be deprecated with little notice.

## 4. Frontend Plan (build after backend)

**Stack:** Next.js (React) — covers both the dashboard and the marketing site in one codebase.

### Dashboard shell

- Auth (login/signup, JWT in an httpOnly cookie)
- Business switcher, wired for multi-tenancy even with one business initially

### Conversations view

- List of active/recent conversations with lead status badges
- Thread view showing the AI's messages — needed to debug agent behavior and build owner trust
- Manual takeover button (send as human, pause AI on that thread) — the UI for "escalate to human"

### Metrics dashboard

- Leads contacted, qualified, appointments booked, recovered leads, estimated revenue
- Simple charts (e.g. recharts) — bar/line over time, kept simple at first

### Settings

- Knowledge base editor (services, pricing, FAQs)
- Follow-up cadence config (delays, message templates)
- Calendar connection (Google OAuth)
- WhatsApp number connection

### Marketing/landing page

Build this last — once a pilot clinic produces real numbers, a landing page built around actual results ("Recovered 18 leads, $24,600 in bookings") is far stronger than one built around a mockup.

## 5. Phased Build Plan

**Phase 1 — Core loop (2–3 weeks)**
FastAPI backend, Postgres schema, WhatsApp webhook, knowledge base, LLM tool-calling loop, Google Calendar integration.

**Phase 2 — Follow-up engine (1–2 weeks)**
Celery beat job for stale conversations, configurable follow-up sequence, lead status states.

**Phase 3 — Dashboard (1–2 weeks)**
Next.js dashboard with core metrics; business settings page for knowledge base and follow-up cadence.

**Phase 4 — Pilot with real dental clinics**
Onboard 2–3 clinics manually, connect real WhatsApp/website channels, monitor conversations closely, tune prompts and tools.

**Phase 5 — Multi-channel + tiers**
Add Instagram DMs and email; wire pricing tiers to feature flags (channel count, agent count, analytics access).

> Recommendation: cut Instagram and email from the MVP entirely. WhatsApp + website chat is enough to prove the loop with the first dental clinic, and Instagram's API has more approval friction than WhatsApp Cloud API.

## 6. Name Suggestions

Since the niche launch is dental but the long-term plan is multi-vertical, names that evoke the outcome (bookings, revenue, follow-up) travel better than dental-specific puns.

- **Followly** — generic enough to survive expansion beyond dental; describes the core follow-up mechanic directly.
- **Rebook** — direct, describes the recovery/follow-up mechanic well.
- **LeadChair** — dental-flavored but reads fine for any appointment-based business (salons, med spas).
- **Clinch** — as in "clinch the appointment/sale."
- **Fillo** — dental pun (filling appointments/cavities); catchy for the initial dental pitch, limits later expansion.
- **Chairful** — dental pun (filling the chair); same trade-off as Fillo.

If keeping one name through all future verticals matters more than a punchy dental-specific pitch, **Followly** or **Rebook** are the safer picks. For a catchy cold-pitch to a dentist now with a rebrand planned later, **Fillo** or **Chairful** work well.