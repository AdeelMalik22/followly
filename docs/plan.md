# Followly Development Plan

*AI Sales Follow-Up Agent - Phased Implementation*

Generated: 2026-08-26

## Development Guidelines

**Token Efficiency Protocol:** Minimize verbose explanations. Prioritize working code over commentary. Brief status updates only. Let code and commits speak for themselves.

## Overview

Building an AI agent that connects to WhatsApp, Instagram, email, and website chat to automatically qualify leads, book appointments, and follow up with prospects for small businesses (starting with dental clinics).

**Core Value Proposition:** Autonomous revenue agent that converts more leads into booked appointments without manual intervention.

## Tech Stack Summary

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Backend API | FastAPI (Python) | Async-native, handles concurrent webhooks/LLM calls |
| Database | PostgreSQL | Relational data for conversations, leads, appointments |
| Task Queue | Celery + Redis | Scheduled follow-ups, reminders, async jobs |
| LLM Layer | OpenRouter → swappable | Start free, switch to Anthropic/OpenAI later |
| Frontend | Next.js (React) | Unified marketing + dashboard |
| Calendar | Google Calendar API | Availability checking and booking |
| Messaging | WhatsApp Cloud API (MVP) | Primary channel for dental clinics |
| Deployment | Render/Railway free tier | Low-cost until revenue |

## Phase 1: Backend Foundation (Week 1-3)

### 1.1 Project Setup
- [ ] Initialize FastAPI project structure
  ```
  followly/
  ├── app/
  │   ├── api/          # API endpoints
  │   ├── models/       # SQLAlchemy models
  │   ├── services/     # Business logic
  │   ├── tasks/        # Celery tasks
  │   ├── llm/          # LLM client & config
  │   └── core/         # Config, deps, auth
  ├── alembic/          # DB migrations
  ├── tests/
  └── .env
  ```
- [ ] Setup PostgreSQL locally
- [ ] Configure Alembic for migrations
- [ ] Setup Redis locally
- [ ] Create `.env.example` with all required vars

### 1.2 Database Schema
- [ ] **Business** model: id, name, created_at, settings (JSONB)
- [ ] **User** model: id, business_id, email, hashed_password, role
- [ ] **Lead** model: id, business_id, phone, name, email, status, source, metadata
- [ ] **Conversation** model: id, business_id, lead_id, channel, status, last_message_at
- [ ] **Message** model: id, conversation_id, role (user/assistant/system), content, timestamp
- [ ] **Appointment** model: id, business_id, lead_id, calendar_event_id, start_time, end_time, service, status
- [ ] **KnowledgeBaseEntry** model: id, business_id, category, question, answer, metadata
- [ ] **FollowUpRule** model: id, business_id, trigger_condition, delay_hours, message_template, active
- [ ] Create initial migration
- [ ] Add indexes: business_id on all tables, lead phone/email, conversation status

### 1.3 Authentication & Multi-Tenancy
- [ ] JWT auth implementation (login/signup endpoints)
- [ ] Middleware to extract business_id from JWT
- [ ] Dependency injection for current_user, current_business
- [ ] Role-based access (owner/admin/agent roles for future)
- [ ] Test multi-tenant data isolation

### 1.4 LLM Layer (Swappable Provider)
- [ ] Create `llm/config.py` with PROVIDER_DEFAULTS dict
- [ ] Implement `load_llm_config()` reading from env
- [ ] Create `llm/client.py` with cached client initialization
- [ ] Implement `chat()` wrapper function
- [ ] Test with OpenRouter free model (llama-3.1-8b-instruct:free)
- [ ] Add error handling and retry logic
- [ ] Add fallback model list for rate limit handling

### 1.5 Knowledge Base CRUD
- [ ] POST `/api/v1/knowledge` - Create entry
- [ ] GET `/api/v1/knowledge` - List entries for business
- [ ] PUT `/api/v1/knowledge/{id}` - Update entry
- [ ] DELETE `/api/v1/knowledge/{id}` - Delete entry
- [ ] Service layer to inject relevant KB into system prompt
- [ ] Test with sample dental services/pricing data

### 1.6 WhatsApp Integration
- [ ] Register Meta Developer account
- [ ] Create test WhatsApp Business API app
- [ ] Implement webhook verification endpoint
- [ ] Implement webhook message receiver
- [ ] Store business WhatsApp credentials in Business.settings
- [ ] Implement WhatsApp message sender
- [ ] Test with test number → verify send/receive loop

### 1.7 Conversation Engine (Core AI Loop)
- [ ] Create `services/agent.py` with main conversation handler
- [ ] Load conversation history (last 20 messages)
- [ ] Load relevant knowledge base entries
- [ ] Build system prompt template (dental clinic persona)
- [ ] Define tool schemas:
  - `check_availability(date, duration)` → Google Calendar
  - `book_appointment(lead_id, start_time, service)` → Create appointment + calendar event
  - `reschedule_appointment(appointment_id, new_start_time)` → Update both
  - `cancel_appointment(appointment_id, reason)` → Cancel + update calendar
  - `escalate_to_human(reason)` → Set conversation.status = 'human_takeover'
- [ ] Implement tool calling loop:
  1. Call LLM with tools
  2. Execute tool calls
  3. Feed results back to LLM
  4. Get final response
  5. Send via WhatsApp
- [ ] Store all messages in DB
- [ ] Update lead status based on conversation progress
- [ ] Test full conversation flow via Postman/curl

### 1.8 Google Calendar Integration
- [ ] Setup Google Cloud project + OAuth 2.0 credentials
- [ ] Implement OAuth flow for calendar connection
- [ ] Store refresh token in Business.settings (encrypted)
- [ ] Implement `check_availability()` - query free/busy
- [ ] Implement `create_event()` - book appointment
- [ ] Implement `update_event()` - reschedule
- [ ] Implement `delete_event()` - cancel
- [ ] Handle calendar API errors gracefully
- [ ] Test with test Google account

### 1.9 Testing & Logging
- [ ] Setup structured logging (JSON logs per conversation)
- [ ] Add conversation_id to all log entries
- [ ] Create test fixtures for Business, Lead, Conversation
- [ ] Write tests for agent loop with mocked LLM
- [ ] Write tests for tool execution
- [ ] Test multi-turn conversations
- [ ] Test error recovery (LLM timeout, calendar API down)

## Phase 2: Follow-Up Engine (Week 4-5)

### 2.1 Lead Status State Machine
- [ ] Define states: new → contacted → qualified → booked / cold → recovered
- [ ] Implement status transition logic in `services/lead.py`
- [ ] Auto-transition based on conversation milestones:
  - new → contacted: first AI response sent
  - contacted → qualified: lead provides phone/service interest
  - qualified → booked: appointment created
  - contacted → cold: no response after 48h
  - cold → recovered: responds after follow-up
- [ ] Add status field to Lead model if not already present

### 2.2 Celery Setup
- [ ] Configure Celery app with Redis broker
- [ ] Create `tasks/follow_up.py`
- [ ] Setup Celery beat scheduler
- [ ] Test task execution locally

### 2.3 Follow-Up Logic
- [ ] Create scheduled task: `scan_stale_conversations()`
  - Runs every 30 minutes
  - Finds conversations with no reply > configured delay
  - Marks leads as needing follow-up
- [ ] Create task: `send_follow_up(conversation_id, message_template_id)`
  - Load conversation context
  - Generate personalized follow-up using LLM
  - Send via appropriate channel
  - Update last_follow_up timestamp
- [ ] Implement follow-up sequence (3 messages max):
  1. Day 1: "Hi [name], just checking if you had questions about [service]?"
  2. Day 3: Value reminder + social proof
  3. Day 7: Last chance / special offer
- [ ] Stop follow-ups if lead responds or marks as "not interested"

### 2.4 Cold Lead Reactivation
- [ ] Create task: `reactivate_cold_leads()`
  - Runs weekly
  - Finds leads with status=cold, last_contact > 30 days
  - Sends reactivation message (new promotions, check-in)
- [ ] Track reactivation attempts (max 2 per lead)
- [ ] Measure recovered → booked conversion

### 2.5 Follow-Up Configuration API
- [ ] GET `/api/v1/follow-up-rules` - List rules
- [ ] POST `/api/v1/follow-up-rules` - Create rule
- [ ] PUT `/api/v1/follow-up-rules/{id}` - Update rule
- [ ] Enable/disable rules per business
- [ ] Default rule templates for dental clinics

### 2.6 Testing
- [ ] Mock time to test delay triggers
- [ ] Test follow-up sequence execution
- [ ] Test follow-up stops on user reply
- [ ] Test cold lead reactivation logic
- [ ] Verify Celery beat scheduling

## Phase 3: Dashboard Frontend (Week 6-7)

### 3.1 Next.js Setup
- [ ] Initialize Next.js project (App Router)
- [ ] Setup Tailwind CSS
- [ ] Install dependencies: recharts, react-query, zustand
- [ ] Configure API base URL
- [ ] Setup TypeScript types for API responses

### 3.2 Authentication UI
- [ ] Login page (`/login`)
- [ ] Signup page (`/signup`)
- [ ] JWT storage in httpOnly cookie (via API route handler)
- [ ] Auth context provider
- [ ] Protected route wrapper
- [ ] Logout functionality

### 3.3 Dashboard Layout
- [ ] Sidebar navigation component
  - Dashboard (metrics)
  - Conversations
  - Leads
  - Settings
  - Logout
- [ ] Header with business name + user menu
- [ ] Mobile responsive navigation

### 3.4 Metrics Dashboard (`/dashboard`)
- [ ] Fetch metrics from `/api/v1/metrics`
- [ ] Stat cards:
  - Leads contacted (this month)
  - Leads qualified
  - Appointments booked
  - Recovered leads
  - Estimated revenue
- [ ] Line chart: leads over time (last 30 days)
- [ ] Bar chart: appointments by service type
- [ ] Conversion funnel visualization
- [ ] Date range selector

### 3.5 Conversations View (`/conversations`)
- [ ] List view with filters (active/cold/booked/all)
- [ ] Lead status badges
- [ ] Search by lead name/phone
- [ ] Pagination
- [ ] Click to open thread view

### 3.6 Thread View (`/conversations/[id]`)
- [ ] Display full conversation history
- [ ] Message bubbles (user vs AI)
- [ ] Timestamps
- [ ] Lead info sidebar (name, phone, status, source)
- [ ] Manual takeover button:
  - Pauses AI on this thread
  - Opens input for human response
  - Sends message as business owner
- [ ] Resume AI button
- [ ] Mark lead as "not interested" button

### 3.7 Leads View (`/leads`)
- [ ] Table view: name, phone, status, source, last_contact, actions
- [ ] Filters by status
- [ ] Search
- [ ] Pagination
- [ ] Click row to open conversation
- [ ] Manual lead creation form

### 3.8 Settings View (`/settings`)
- [ ] **Knowledge Base tab:**
  - List services/pricing/FAQs
  - Add/edit/delete entries
  - Category selector (services, pricing, policies, FAQs)
- [ ] **Calendar Connection tab:**
  - Google OAuth connect button
  - Show connected calendar email
  - Disconnect option
  - Business hours configuration
- [ ] **Follow-Up Rules tab:**
  - List active rules
  - Toggle enable/disable
  - Edit delay and message templates
  - Create new rule
- [ ] **WhatsApp Connection tab:**
  - Connection status
  - Test message button
  - Webhook URL display for manual setup
- [ ] **Business Profile tab:**
  - Business name, address, phone
  - Logo upload (future)

### 3.9 Testing
- [ ] Test auth flow (login, logout, token refresh)
- [ ] Test all CRUD operations from UI
- [ ] Responsive design check (mobile, tablet, desktop)
- [ ] Error state handling (API down, validation errors)
- [ ] Loading states for all async operations

## Phase 4: Pilot Launch (Week 8-10)

### 4.1 Deployment
- [ ] Setup production Postgres database (Render/Railway)
- [ ] Setup production Redis (Render/Railway or Upstash)
- [ ] Deploy backend to Render/Railway
- [ ] Setup environment variables in production
- [ ] Deploy frontend to Vercel
- [ ] Setup custom domain (followly.app or similar)
- [ ] SSL certificates
- [ ] Setup monitoring (Sentry for errors)

### 4.2 Production Readiness
- [ ] Add rate limiting to webhook endpoints (requestguard library)
- [ ] Add request logging middleware
- [ ] Setup backup strategy for database
- [ ] Create admin scripts for manual operations
- [ ] Document deployment process
- [ ] Setup CI/CD pipeline (GitHub Actions)

### 4.3 Pilot Recruitment
- [ ] Identify 2-3 dental clinics in local area
- [ ] Prepare pitch deck with mockup metrics
- [ ] Offer free 3-month pilot in exchange for feedback
- [ ] Schedule demo calls

### 4.4 Manual Onboarding (Pilot Clinics)
- [ ] Create business account for clinic
- [ ] Connect clinic's WhatsApp Business number (verify webhook)
- [ ] Connect Google Calendar (OAuth flow)
- [ ] Populate knowledge base:
  - Services offered (cleaning, whitening, implants, etc.)
  - Pricing for each service
  - Office hours
  - Insurance accepted
  - Common FAQs
- [ ] Configure follow-up rules (test conservative delays first)
- [ ] Test full conversation flow with test leads
- [ ] Train clinic staff on dashboard usage (takeover, lead review)

### 4.5 Monitoring & Iteration
- [ ] Daily check of conversation logs (first 2 weeks)
- [ ] Monitor for AI failures:
  - Hallucinated information
  - Failed tool calls
  - Inappropriate responses
  - Escalation triggers not working
- [ ] Weekly metrics review with pilot clinics
- [ ] Collect qualitative feedback:
  - What questions does AI struggle with?
  - Are follow-ups too aggressive/passive?
  - What features are missing?
- [ ] Iterate on system prompt based on real conversations
- [ ] Tune follow-up timing based on response rates
- [ ] Add missing knowledge base entries as gaps are discovered

### 4.6 Success Metrics (Pilot Phase)
- [ ] Track for each clinic:
  - Total leads contacted
  - Qualification rate (% of leads that engage)
  - Booking rate (% of qualified leads that book)
  - Follow-up response rate
  - Cold lead recovery rate
  - Revenue attributed to AI bookings
- [ ] Target: 20%+ booking rate from qualified leads
- [ ] Target: 10%+ cold lead recovery rate
- [ ] Gather testimonials if results are strong

## Phase 5: Multi-Channel & Scaling (Week 11-14)

### 5.1 Website Chat Widget
- [ ] Create embeddable chat widget (React component)
- [ ] Widget backend endpoint (`POST /api/v1/widget/message`)
- [ ] Widget authentication (business API key)
- [ ] Widget customization (colors, position, branding)
- [ ] Installation instructions for clinic websites
- [ ] Test on sample dental clinic website

### 5.2 Instagram DMs (Optional - high friction)
- [ ] Apply for Instagram Messaging API access
- [ ] Implement Instagram webhook handler
- [ ] Implement Instagram message sender
- [ ] Connect Instagram account in settings UI
- [ ] Test with pilot clinic Instagram account

### 5.3 Email Integration (Optional)
- [ ] IMAP integration for reading emails
- [ ] SMTP integration for sending emails
- [ ] Email parsing to extract lead info
- [ ] Thread detection (group related emails)
- [ ] HTML email template for responses
- [ ] Connect Gmail/Outlook in settings UI

### 5.4 Pricing Tiers Implementation
- [ ] Add `subscription_tier` to Business model (starter/growth/pro)
- [ ] Add `subscription_status` (trial/active/cancelled)
- [ ] Feature flags based on tier:
  - Starter: 1 channel (WhatsApp or website)
  - Growth: Multi-channel + calendar + CRM + follow-ups
  - Pro: All features + analytics + custom workflows
- [ ] Usage tracking (messages sent per month)
- [ ] Usage limit enforcement
- [ ] Upgrade/downgrade UI in dashboard

### 5.5 Payment Integration
- [ ] Stripe account setup
- [ ] Stripe Checkout integration (subscription)
- [ ] Webhook handler for Stripe events (payment success/failure)
- [ ] Update subscription_status based on payment
- [ ] Billing page in dashboard (invoices, payment method)
- [ ] Trial period logic (14 days free)
- [ ] Cancellation flow

### 5.6 Marketing Website
- [ ] Landing page (`/`) with:
  - Hero: "Convert More Leads Into Booked Appointments"
  - Problem statement (missed leads, slow follow-up)
  - Solution overview (AI agent that never sleeps)
  - Real metrics from pilot clinics
  - How it works (3-step visual)
  - Pricing table
  - Testimonials from pilot clinics
  - FAQ
  - CTA: Start Free Trial
- [ ] Demo booking page (`/demo`)
- [ ] Blog setup (future content marketing)
- [ ] SEO optimization (meta tags, sitemap, robots.txt)

### 5.7 Self-Service Signup
- [ ] Signup flow with Stripe trial checkout
- [ ] Onboarding wizard:
  1. Business info (name, type, address)
  2. Connect WhatsApp (step-by-step guide)
  3. Connect calendar
  4. Add first knowledge base entries (guided prompts)
  5. Send test message
- [ ] Email drip campaign for new signups (onboarding tips)
- [ ] Admin dashboard for viewing all businesses

## Phase 6: Advanced Features (Week 15+)

### 6.1 Analytics & Insights
- [ ] Conversation analytics:
  - Average response time
  - Common questions
  - Drop-off points in conversation
- [ ] A/B testing for follow-up messages
- [ ] Lead source attribution
- [ ] Export to CSV

### 6.2 CRM Integration
- [ ] Zapier integration (webhook triggers)
- [ ] Direct integrations (HubSpot, Salesforce) for enterprise tier
- [ ] Sync leads and appointments to external CRM

### 6.3 Multi-Agent Support (Pro Tier)
- [ ] Add agent personality customization
- [ ] Multiple agents per business (e.g., one for bookings, one for FAQs)
- [ ] Agent performance comparison

### 6.4 Voice & SMS
- [ ] Twilio integration for SMS
- [ ] Twilio Voice API for inbound/outbound calls
- [ ] Voice-to-text for call handling

### 6.5 Advanced Workflows
- [ ] Visual workflow builder (if/then rules)
- [ ] Custom follow-up sequences per service type
- [ ] Tag-based automation
- [ ] Lead scoring

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Free LLM models unreliable | High | Add fallback model list; budget for paid tier early |
| WhatsApp API gets blocked | High | Follow Meta policies strictly; have backup channels ready |
| Pilot clinics see low conversion | High | Over-index on prompt tuning; offer manual takeover early |
| Calendar sync fails intermittently | Medium | Add retry logic + manual booking fallback in UI |
| AI hallucinates pricing/policies | Critical | Strict KB injection; add "I don't know" fallback prompt |
| User confusion with manual takeover | Medium | Add in-app tutorial; proactive support in pilot phase |
| Regulatory/compliance (HIPAA for dental) | High | Don't store PII unnecessarily; add compliance disclaimer; consult legal |

## Success Criteria (End of Pilot)

- [ ] 2-3 dental clinics actively using system for 30+ days
- [ ] 50+ real leads processed through AI
- [ ] 15%+ booking rate from qualified leads
- [ ] Zero major AI hallucinations or inappropriate responses
- [ ] Positive testimonials from at least 2 pilot clinics
- [ ] Clear pricing validated (pilot clinics willing to pay)

## Next Steps After Pilot

1. Expand to 10 paying dental clinics (validate revenue)
2. Add second vertical (med spas or salons)
3. Build referral program for clinics to invite peers
4. Raise pre-seed funding or continue bootstrapping
5. Hire first engineer/designer

---

**Estimated Timeline:** 14-16 weeks from start to pilot completion

**Immediate Next Action:** Initialize FastAPI project structure and setup local development environment.
