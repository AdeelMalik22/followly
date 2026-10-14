"""Backfill dedicated tenant configuration and remove credential copies."""

from alembic import op
import sqlalchemy as sa


revision = "p1k2l3m4n5o6"
down_revision = "o0j1k2l3m4n5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    businesses = sa.table(
        "businesses",
        sa.column("id", sa.Integer()),
        sa.column("settings", sa.JSON()),
        sa.column("configuration", sa.JSON()),
        sa.column("whatsapp_access_token", sa.String()),
        sa.column("google_calendar_credentials", sa.JSON()),
    )
    connection = op.get_bind()
    rows = connection.execute(sa.select(
        businesses.c.id,
        businesses.c.settings,
        businesses.c.configuration,
        businesses.c.whatsapp_access_token,
        businesses.c.google_calendar_credentials,
    )).fetchall()
    for business_id, settings, configuration, whatsapp_token, calendar_credentials in rows:
        legacy = settings if isinstance(settings, dict) else {}
        values = {}
        if configuration is None:
            values["configuration"] = {
                "agent": legacy.get("agent") or {},
                "branding": legacy.get("branding") or {},
                "escalation": legacy.get("escalation") or {},
                "channels": legacy.get("channels") or {},
                "booking": {
                    "working_hours": legacy.get("working_hours", {}),
                    "appointment_duration_minutes": legacy.get("appointment_duration_minutes", 60),
                },
            }
        if calendar_credentials is None and legacy.get("google_calendar_credentials"):
            values["google_calendar_credentials"] = legacy["google_calendar_credentials"]
        cleaned = dict(legacy)
        cleaned.pop("whatsapp_access_token", None)
        cleaned.pop("google_calendar_credentials", None)
        if cleaned != legacy:
            values["settings"] = cleaned
        if values:
            connection.execute(businesses.update().where(businesses.c.id == business_id).values(**values))


def downgrade() -> None:
    pass
