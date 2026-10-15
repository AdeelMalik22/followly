# Followly frontend plan

## Product direction

Followly should feel like a calm, premium CRM for business owners. The visual
language is light and spacious: white surfaces, navy typography, pale blue
backgrounds, indigo primary actions, emerald success states, rounded cards, and
small meaningful data visualizations. The interface should make the AI feel
useful and approachable rather than futuristic or technical.

## Phase 1 — Shared visual foundation

- Finish the light dashboard shell and responsive sidebar.
- Create reusable design tokens for colors, spacing, radius, shadows, type, and
  states.
- Build shared components: buttons, cards, badges, tabs, tables, filters,
  modals, drawers, empty states, loading states, error states, and toast
  notifications.
- Add a consistent mobile navigation pattern.
- Add a reusable page header with title, description, search, filters, and
  primary action.
- Replace scattered dark-theme classes with shared light-theme components.

Exit criteria: every dashboard route uses the same shell and component styles,
works at desktop and mobile widths, and has loading, empty, and error states.

## Phase 2 — Authentication and onboarding

- Redesign landing page with the Followly value proposition and product proof.
- Redesign login and signup around a simple two-column SaaS layout.
- Add password recovery and reset screens.
- Build the onboarding wizard for business details, AI tone, channels,
  knowledge, working hours, review, and launch.
- Show setup progress and allow saving and resuming.

Exit criteria: a new business can sign up, complete onboarding, recover an
account, and reach the dashboard without developer assistance.

## Phase 3 — CRM workspace

- Redesign dashboard overview with:
  - Welcome banner.
  - New leads, conversations, appointments, response rate, follow-ups, and AI
    usage cards.
  - Customer journey funnel.
  - Recent conversations.
  - Upcoming appointments.
  - AI agent status.
  - Integration status.
  - Plan usage summary.
- Redesign Leads as a searchable, filterable table with lead detail drawer,
  status changes, notes, tags, and delete confirmation.
- Redesign Conversations as a three-pane inbox with filters, contact details,
  AI suggestions, notes, and reply composer.
- Redesign Appointments as month, week, and day calendar views with upcoming
  appointment list and calendar connection status.

Exit criteria: the core CRM workflow from lead capture to conversation to
appointment is clear and usable on desktop and tablet.

## Phase 4 — AI agent and knowledge

- Build the AI Agent page with configuration tabs for tone, language, behavior,
  instructions, tools, and test chat.
- Show live preview and test scenarios for FAQ, pricing, booking, and escalation.
- Redesign Knowledge Base with source cards, ingestion progress, search,
  visibility, document preview, and version history.
- Add clear empty states that guide the business toward its first useful setup.

Exit criteria: a business can configure, test, and improve its agent using only
the dashboard.

## Phase 5 — Automation and integrations

- Redesign Follow-up Automation with workflow cards, status toggles, trigger
  and action builder, and performance summaries.
- Redesign Channels and Integrations with separate communication and calendar
  sections.
- Show connected, disconnected, error, reconnect, and pending states.
- Add widget installation instructions and copyable embed code.

Exit criteria: a business can connect channels, configure an automation, and
understand the health of each integration.

## Phase 6 — Team, billing, and settings

- Redesign Team Management with members, pending invitations, roles,
  permissions, removal, and owner transfer flows.
- Redesign Billing with current plan, payment state, plan comparison, upgrade,
  downgrade, cancellation, renewal, payment failure, and invoice history.
- Add Usage and Plan Limits with progress bars, trend charts, limit warnings,
  and usage-period dates.
- Redesign Settings with business profile, branding, terminology, working
  hours, channels, security, sessions, and configuration audit history.

Exit criteria: business owners can manage their team, subscription, limits,
branding, security, and configuration from the dashboard.

## Phase 7 — Quality and release readiness

- Add responsive checks at mobile, tablet, and desktop breakpoints.
- Add accessible keyboard navigation, focus states, labels, and contrast.
- Add route-level error and loading boundaries.
- Add frontend API error handling for expired sessions, plan limits, provider
  failures, and validation errors.
- Add Playwright or equivalent browser tests for signup, onboarding, dashboard,
  lead creation, test chat, billing, and logout.
- Run TypeScript, ESLint, production build, and browser tests before release.

## Delivery order

Each visual feature should be committed separately:

1. Shared shell and design system.
2. Authentication and onboarding.
3. Dashboard overview.
4. Leads and conversations.
5. Appointments and knowledge.
6. AI Agent and automations.
7. Channels and integrations.
8. Team, billing, usage, and settings.
9. Responsive, accessibility, and browser-test hardening.
