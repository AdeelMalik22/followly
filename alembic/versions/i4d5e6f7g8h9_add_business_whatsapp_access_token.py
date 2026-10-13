"""Promote the encrypted WhatsApp token to a dedicated business column."""

from alembic import op
import sqlalchemy as sa


revision = "i4d5e6f7g8h9"
down_revision = "h3c4d5e6f7g8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("businesses", sa.Column("whatsapp_access_token", sa.String(), nullable=True))

    businesses = sa.table(
        "businesses",
        sa.column("id", sa.Integer()),
        sa.column("settings", sa.JSON()),
        sa.column("whatsapp_access_token", sa.String()),
    )
    connection = op.get_bind()
    rows = connection.execute(sa.select(businesses.c.id, businesses.c.settings)).fetchall()
    for business_id, settings in rows:
        token = (settings or {}).get("whatsapp_access_token") if isinstance(settings, dict) else None
        if token:
            connection.execute(
                businesses.update()
                .where(businesses.c.id == business_id)
                .values(whatsapp_access_token=token)
            )


def downgrade() -> None:
    op.drop_column("businesses", "whatsapp_access_token")
