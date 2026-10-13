"""Promote Google Calendar credentials to a dedicated business column."""

from alembic import op
import sqlalchemy as sa


revision = "j5e6f7g8h9i0"
down_revision = "i4d5e6f7g8h9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("businesses", sa.Column("google_calendar_credentials", sa.JSON(), nullable=True))

    businesses = sa.table(
        "businesses",
        sa.column("id", sa.Integer()),
        sa.column("settings", sa.JSON()),
        sa.column("google_calendar_credentials", sa.JSON()),
    )
    connection = op.get_bind()
    rows = connection.execute(sa.select(businesses.c.id, businesses.c.settings)).fetchall()
    for business_id, settings in rows:
        credentials = (settings or {}).get("google_calendar_credentials") if isinstance(settings, dict) else None
        if credentials:
            connection.execute(
                businesses.update()
                .where(businesses.c.id == business_id)
                .values(google_calendar_credentials=credentials)
            )


def downgrade() -> None:
    op.drop_column("businesses", "google_calendar_credentials")
