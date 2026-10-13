# Followly SaaS Transition Plan

## Purpose

Transform Followly from a clinic-focused AI agent into a production-ready, multi-tenant SaaS platform. The existing application remains the baseline: FastAPI, SQLAlchemy, PostgreSQL, Redis/Celery configuration, JWT authentication, a Next.js dashboard, website chat, WhatsApp, Google Calendar, billing, knowledge management, and a shared conversation engine.

The transition will be incremental. Each phase must preserve working behavior, include focused tests, and be deployable or reviewable before the next phase begins.

## Current baseline

- `Business` already acts as the tenant root and owns users, leads, conversations, appointments, knowledge entries, follow-up rules, and customers.
- Business users authenticate with JWTs containing the user and business identity.
- Customer Google OAuth creates business-scoped customer records and a customer JWT cookie.
- Dashboard routes generally use `get_current_business()` for tenant context.
- Public chat and webhook routes resolve a business from a widget key or channel data and pass the business into the agent engine.
- Agent behavior is assembled from business data in `agent_service.py` and executed through `conversation_engine.py`.
- WhatsApp credentials are encrypted before storage.
- Alembic migrations and an initial multi-business test already exist.
- The frontend contains dashboard areas for onboarding, settings, knowledge, leads, conversations, appointments, channels, follow-up, and team management.

## Phase 0 — Architecture inventory and safety baseline

Goal: establish an accurate map of the current system before changing its boundaries.

Work:

- Document every API route, dependency, model relationship, migration, service, background task, frontend dashboard area, and external integration.
- Trace the tenant identity through authenticated dashboard requests, customer chat, Google OAuth, WhatsApp webhooks, calendar callbacks, billing, and agent tool calls.
- Identify routes that query records by ID without also filtering by `business_id`.
- Identify global configuration or credentials that must become business-specific.
- Record existing test coverage and add a repeatable test database setup.
- Define the supported tenant states: onboarding, active, suspended, trial, subscribed, and cancelled.

Exit criteria:

- An endpoint-to-tenant-context inventory is checked into the repository.
- Every known business-owned model and access path has an owner and isolation strategy.
- Existing tests pass before migration work begins.

## Phase 1 — Tenant identity and authorization hardening

Goal: make tenant isolation explicit and consistent across all protected operations.

Work:

- Keep `Business` as the tenant root unless the inventory proves a separate tenant entity is required.
- Centralize authenticated user and business resolution in dependencies or service helpers.
- Require all dashboard reads, writes, updates, deletes, analytics, exports, and tool operations to use the authorized business context.
- Remove any reliance on client-supplied `business_id` for authorization.
- Scope record lookups by both record ID and the authorized business ID.
- Add database constraints and indexes for business-owned foreign keys and public identifiers.
- Make the widget key a first-class unique public identifier, or introduce a safe migration to one if keeping it in JSON is temporarily necessary.
- Define authorization roles and permissions for owners, admins, and staff before enabling team management.
- Review customer JWT claims and public chat authorization so a token cannot be reused with another business key.

Tests:

- Create two businesses with equivalent records and prove that cross-tenant reads, updates, deletes, conversations, knowledge searches, analytics, calendar actions, and lead operations fail.
- Test forged and mismatched business IDs in request bodies, path parameters, query parameters, JWTs, widget keys, and webhook payloads.
- Test role restrictions for owner, admin, and staff operations.

Exit criteria:

- Cross-tenant isolation tests pass for every protected route.
- No protected route authorizes access from a client-provided business ID alone.

## Phase 2 — Tenant configuration and domain model

Goal: separate business configuration from shared application configuration.

Work:

- Introduce explicit tenant-owned configuration for agent instructions, tone, language, welcome message, escalation rules, branding, widget settings, business hours, booking settings, and enabled channels.
- Keep secrets out of general JSON settings where practical; use dedicated encrypted credential storage for OAuth, WhatsApp, and payment credentials.
- Add subscription, plan, usage limit, and usage counter models only where the existing billing model does not cover the requirement.
- Add lifecycle fields and audit timestamps to business-owned configuration.
- Define safe defaults and validation for new businesses.
- Add migrations with backward-compatible data backfills from the current `Business.settings` JSON.

Exit criteria:

- A new business can be created without source-code changes.
- Existing businesses retain their current agent behavior after migration.
- Configuration reads and writes are tenant-scoped and validated.

## Phase 3 — Agent and knowledge tenancy

Goal: ensure every AI response uses only the selected business’s configuration and knowledge.

Work:

- Refactor agent prompt construction to receive a tenant context explicitly.
- Scope knowledge creation, retrieval, updates, deletion, and search by business ID.
- Add a document ingestion model and status lifecycle if uploads and asynchronous processing are introduced.
- Add source metadata, versioning, visibility, and deletion handling for knowledge records.
- Namespace any cache keys, vector indexes, retrieval results, and background jobs by business ID.
- Ensure tool calls receive the same tenant context as the originating conversation.
- Add usage accounting for LLM requests, tool calls, tokens, and failures.

Tests:

- Verify identical questions from two businesses retrieve different knowledge.
- Verify a tool call cannot book, cancel, or inspect an appointment belonging to another business.
- Verify cache hits never return another tenant’s prompt or retrieval data.

Exit criteria:

- Agent output and tool execution are tenant-specific by construction.
- Knowledge and retrieval isolation tests pass.

## Phase 4 — Channel and integration isolation

Goal: make every communication channel safely multi-tenant.

Work:

- Define how each webhook identifies a business and validate that mapping before processing.
- Make webhook idempotency keys tenant-aware and persist inbound event processing state.
- Store channel credentials per business with encryption, rotation, and redacted logging.
- Scope Google Calendar OAuth state, stored credentials, events, and callbacks by business.
- Scope WhatsApp send operations, phone number IDs, access tokens, and webhook signatures by business.
- Complete website widget installation using a public widget identifier and tenant-safe API surface.
- Add integration health status, reconnect, disconnect, and failure recovery behavior.

Exit criteria:

- A channel event cannot be routed to the wrong business.
- One business cannot send through another business’s credentials.
- Replayed and duplicate webhook events are handled safely.

## Phase 5 — Product onboarding and dashboard workflows

Goal: allow a business to register, configure, test, and launch without developer intervention.

Work:

- Complete onboarding for business profile, industry, agent instructions, business hours, knowledge, branding, and channels.
- Add a dashboard test chat that uses the current business context.
- Add widget installation instructions and generated embed configuration.
- Add team invitations, role management, account recovery, and session management.
- Add tenant-specific usage, limits, subscription state, and billing status to the dashboard.
- Replace assumptions that every business is a dental clinic with configurable industry and terminology.

Exit criteria:

- A new business can complete onboarding and launch a widget using only dashboard actions.
- The same deployment supports at least two independently configured businesses.

## Phase 6 — Billing, limits, and operational controls

Goal: make the platform commercially operable and protect shared resources.

Work:

- Define plans and entitlements for channels, users, knowledge volume, conversations, messages, and LLM usage.
- Enforce limits at the service boundary with clear user-facing errors.
- Connect Stripe customer, subscription, checkout, and webhook state to the tenant.
- Add usage aggregation and billing-period rollover behavior.
- Add rate limits for public chat, OAuth initiation, webhooks, and dashboard APIs.
- Add abuse controls for widget keys, repeated prompts, and oversized requests.

Exit criteria:

- Usage is attributed to the correct tenant.
- Limits are enforced consistently across dashboard, widget, webhook, and background paths.
- Subscription changes are idempotent and auditable.

## Phase 7 — Production reliability and security

Goal: operate the shared platform safely at production scale.

Work:

- Add structured logs with tenant-safe correlation IDs and no secret or token leakage.
- Add metrics for request errors, latency, LLM usage, queue health, webhook failures, and per-tenant consumption.
- Add health checks for database, Redis, LLM provider, and integrations.
- Add retry policies and dead-letter handling for background work.
- Review cookie flags, CORS, CSRF exposure, OAuth state replay, JWT rotation, secret rotation, and session revocation.
- Evaluate PostgreSQL row-level security after application-level isolation is proven and the deployment model is known.
- Add backups, migration rollback procedures, incident response notes, and data export/deletion workflows.
- Add dependency and secret scanning to CI.

Exit criteria:

- Production deployment has observable failure modes and recovery procedures.
- Security review finds no known cross-tenant access path.
- Migration and rollback procedures are tested against a production-like database.

## Phase 8 — Release and migration

Goal: move existing users and businesses to the SaaS model without service disruption.

Work:

- Create a staging environment with production-like PostgreSQL, Redis, OAuth, Stripe, and channel configuration.
- Run migrations against a copy of production data and verify row counts, foreign keys, tenant assignments, and credentials.
- Run dual-read or compatibility paths where a direct cutover would risk existing chat or webhook traffic.
- Migrate existing settings, widget keys, customer associations, integrations, and subscriptions.
- Perform tenant-by-tenant smoke tests and monitor errors, latency, usage, and webhook delivery.
- Define rollback triggers and retain backups before each irreversible migration.

Exit criteria:

- Existing businesses behave as before.
- New businesses can onboard successfully.
- Cross-tenant security, billing, integration, and recovery checks pass in staging and production.

## Delivery rules

- Make one focused change per commit and push meaningful commits separately.
- Add or update an Alembic migration whenever the data model changes.
- Preserve existing routes and names unless a compatibility layer is provided.
- Run focused tests for each phase, then the full suite before release.
- Do not combine architectural migration with unrelated UI redesigns, dependency upgrades, or speculative abstractions.
- Treat tenant isolation as a release blocker.

## Recommended implementation order

Start with Phase 0 and Phase 1. The current application already has many tenant foreign keys and business-aware dependencies, so the fastest safe path is to audit and harden those boundaries before adding new SaaS features. Then move through configuration, agent tenancy, integrations, onboarding, billing, and operations in that order.

