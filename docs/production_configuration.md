# Production Configuration

Apply the latest Alembic migrations before deploying the application:

```bash
alembic upgrade head
```

## Required security settings

Set a strong, private value for `SECRET_KEY`. Keep `ALGORITHM` aligned across all application instances.

Set `FRONTEND_URL` to the public dashboard URL. Configure `CORS_ORIGINS` with the exact browser origins that may call the API. Multiple origins are comma-separated:

```env
FRONTEND_URL=https://app.example.com
CORS_ORIGINS=https://app.example.com,https://widget.example.com
```

Do not use `*` when authenticated browser requests are enabled.

Set `COOKIE_SECURE=true` when the application is served over HTTPS. Keep it `false` only for local HTTP development.

```env
COOKIE_SECURE=true
```

## Tenant identifiers

`Business.widget_key` and `Business.whatsapp_phone_id` are now dedicated unique, indexed columns. The migrations copy existing values from `Business.settings`.

New business creation and WhatsApp credential updates populate both the dedicated columns and the legacy settings keys for compatibility during the transition.

## OAuth state storage

Customer Google OAuth and Google Calendar OAuth states are stored as hashes in `oauth_states`. States are scoped by business and provider, expire after 10 minutes, and can be consumed once.

All application instances must use the same database. Do not rely on process-local state for OAuth flows.

Expired state cleanup runs when a new state is stored. A periodic database cleanup job can be added later if OAuth traffic is low and long-term table retention becomes a concern.

## OAuth redirect configuration

Register the configured callback URLs with Google and keep the customer and calendar redirect URLs separate:

```env
CUSTOMER_GOOGLE_REDIRECT_URI=https://api.example.com/api/v1/customer/auth/callback
GOOGLE_REDIRECT_URI=https://api.example.com/api/v1/calendar/callback
```

The frontend redirect after successful customer login uses `FRONTEND_URL`.

## Deployment checklist

- Run migrations before starting application workers.
- Verify `DATABASE_URL`, `SECRET_KEY`, `FRONTEND_URL`, and `CORS_ORIGINS` in the deployment environment.
- Set `COOKIE_SECURE=true` behind HTTPS.
- Verify Google OAuth callback URLs match the deployed API hostname.
- Confirm each existing business has a widget key and, where connected, a WhatsApp phone ID.
- Test customer login, calendar connection, website chat, and WhatsApp routing for at least two businesses.
- Confirm the application instances share the same database and encryption configuration.

