# Followly Architecture Inventory

Status: Phase 0 baseline, 2026-10-13

This inventory records the current implementation before the SaaS transition. It is intended to guide tenant-isolation changes and prevent accidental rewrites of working behavior.

## Runtime and deployment components

| Area | Current implementation | Main locations |
|---|---|---|
| HTTP API | FastAPI application with route modules | `app/main.py`, `app/api/` |
| Database | SQLAlchemy ORM, PostgreSQL configured, SQLite used by tests | `app/core/database.py`, `app/models/models.py` |
| Migrations | Alembic | `alembic/` |
| Authentication | JWT bearer tokens for business users; Google OAuth and cookie JWT for customers | `app/core/security.py`, `app/api/auth.py`, `app/api/customer_auth.py` |
| Frontend | Next.js dashboard plus server-rendered login/signup/chat pages | `frontend/`, `app/templates/` |
| AI | Configurable OpenRouter, OpenAI, or Anthropic client | `app/llm/`, `app/services/agent_service.py` |
| Agent workflow | Prompt assembly, conversation history, tool execution, appointment and escalation tools | `app/services/agent_service.py`, `app/services/conversation_engine.py` |
| Queue/cache configuration | Redis is configured; task package exists but current inventory has no active task implementation | `app/core/config.py`, `app/tasks/` |
| Integrations | WhatsApp, Google Calendar, Google customer login, Stripe checkout/status | `app/api/whatsapp.py`, `app/api/calendar.py`, `app/api/customer_auth.py`, `app/api/billing.py` |

## Tenant root and data ownership

`Business` is currently the tenant root. It owns users, leads, conversations, appointments, knowledge entries, customers, and configuration stored in the `settings` JSON column.

| Model | Tenant relationship | Current isolation notes |
|---|---|---|
| `Business` | Root entity | Public widget and integration identifiers are currently stored in `settings`. |
| `User` | `business_id` foreign key | User lookup is by globally unique user ID; business is loaded through the relationship. |
| `Customer` | `business_id` foreign key | Google identity uniqueness is enforced per business. |
| `Lead` | `business_id` and optional `customer_id` | Service helpers receive business ID. |
| `Conversation` | `business_id` and `lead_id` | Route and service queries require review for compound tenant checks. |
| `Message` | Indirectly through `conversation_id` | No direct `business_id`; access must always be through a tenant-scoped conversation. |
| `ToolCallAudit` | Indirectly through `conversation_id` | Access must always be through a tenant-scoped conversation. |
| `Appointment` | `business_id` and `lead_id` | Booking logic receives a business object and checks business availability. |
| `KnowledgeBaseEntry` | `business_id` | Existing tests cover separation between two businesses. |
| `FollowUpRule` | `business_id` | CRUD routes use the authenticated business dependency. |

## Authentication and tenant context

Business users sign up with a business and receive a JWT containing `sub` and `business_id`. Protected dashboard routes use `get_current_user()` and usually `get_current_business()`.

Customer website authentication starts with a business widget key, carries the business ID and OAuth nonce in signed state, and creates a customer JWT containing `customer_id` and `business_id`. Website chat checks that the customer, token business, and widget key agree.

The following areas require hardening in Phase 1:

- Every record lookup by ID should include the authorized business condition where the record is business-owned.
- Public chat currently resolves businesses by scanning all businesses in Python; this is both inefficient and a tenant-boundary hotspot.
- WhatsApp webhook routing scans all businesses by phone ID and must use a unique, indexed tenant mapping.
- Customer chat history and selected conversation IDs need compound checks against the authenticated customer and business.
- OAuth states are signed and expire, but are not currently single-use.
- CORS currently allows all origins while credentials are enabled; production origins must be explicit.

## API surface

### Business-user routes

- Authentication: signup, login, current user.
- Business configuration: profile, onboarding, widget config, escalation settings, booking settings.
- Knowledge: CRUD for business knowledge entries.
- Leads: list, create, and update.
- Conversations: list, detail, messages, update, human messages.
- Appointments: list and create-related operations.
- Analytics: summary and funnel metrics.
- Follow-up rules: CRUD.
- WhatsApp: status, credentials, webhook URL, webhook, and send.
- Calendar: connect, callback, status, disconnect.
- Billing: status and checkout.

### Public or customer routes

- Website chat page and chat message flow.
- Customer Google login, OAuth callback, and logout.
- WhatsApp verification and signed inbound webhook handling.
- Health and root metadata endpoints.

## Main request and agent flows

### Dashboard request

`Authorization` bearer token → `get_current_user()` → `get_current_business()` → route/service query → business-scoped response.

### Website customer chat

Widget key → business resolution → customer cookie validation → customer/business match → lead and conversation resolution → agent prompt and tools → saved messages.

### WhatsApp message

Meta signature validation → payload parsing → business phone ID resolution → lead and conversation resolution → inbound message deduplication → agent processing → encrypted business credential lookup → outbound WhatsApp message.

### Agent request

Conversation and business → business prompt/configuration and knowledge → conversation history → LLM provider → optional business-scoped tools → audit and response persistence.

## Existing verification

`tests/test_multibusiness.py` currently verifies:

- Knowledge entries are separated between two businesses.
- Appointment conflicts are rejected within one business while the same time can be booked by another business.

The suite still needs route-level isolation coverage, forged-ID tests, customer chat isolation tests, webhook routing tests, integration credential tests, and role authorization tests.

## Priority findings for the next implementation phase

1. Build reusable tenant-scoped lookup helpers and apply them to protected routes and services.
2. Replace public identifier scans with unique, indexed tenant identifiers.
3. Add cross-tenant API tests before changing the data model.
4. Move business-specific configuration and credentials out of an unstructured settings blob in incremental migrations.
5. Define explicit frontend origins and production cookie/security settings.

## Phase 0 boundary

This document is an inventory only. It does not change runtime behavior or database schema. Phase 1 should begin with tests and authorization hardening, followed by small, separately committed fixes.

