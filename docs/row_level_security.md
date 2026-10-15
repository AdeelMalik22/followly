# PostgreSQL row-level security evaluation

Followly currently enforces tenant isolation in FastAPI dependencies and every business-owned query. The application uses one shared database connection pool, so enabling RLS immediately would require every transaction to set a trusted tenant context before any business-owned query.

The business-owned tables currently include `users`, `customers`, `leads`, `conversations`, `appointments`, `appointment_status_history`, `knowledge_base`, `knowledge_sources`, `knowledge_versions`, `follow_up_rules`, `usage_events`, `webhook_events`, `oauth_states`, `team_invitations`, `background_jobs`, `stripe_webhook_events`, and `configuration_audits`.

RLS is not enabled by this change because the current request and worker paths do not yet set a PostgreSQL transaction-local value for every connection. Enabling policies before that value is set would either block legitimate work or encourage unsafe bypasses. The application-level isolation review and cross-tenant tests remain the first enforcement layer.

The adoption sequence is:

1. Add a database session hook that executes `SET LOCAL app.business_id = '<validated id>'` after tenant resolution and before business queries.
2. Add equivalent context setup to webhook, OAuth callback, maintenance, and background-job transactions.
3. Create `USING (business_id = current_setting('app.business_id')::integer)` policies for each business-owned table.
4. Keep migrations and administrative maintenance on a separate restricted database role.
5. Run the full cross-tenant suite with RLS enabled in staging, then compare query failures and background-job behavior before production rollout.

The current design has the necessary `business_id` columns and indexes for this migration, but the transaction context propagation step must be completed first.
