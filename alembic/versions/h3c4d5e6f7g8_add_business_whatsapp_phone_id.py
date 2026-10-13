"""Promote the WhatsApp phone ID to an indexed business column."""

from alembic import op
import sqlalchemy as sa


revision = "h3c4d5e6f7g8"
down_revision = "g2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("businesses", sa.Column("whatsapp_phone_id", sa.String(), nullable=True))

    businesses = sa.table(
        "businesses",
        sa.column("id", sa.Integer()),
        sa.column("settings", sa.JSON()),
        sa.column("whatsapp_phone_id", sa.String()),
    )
    connection = op.get_bind()
    rows = connection.execute(sa.select(businesses.c.id, businesses.c.settings)).fetchall()
    for business_id, settings in rows:
        phone_id = (settings or {}).get("whatsapp_phone_id") if isinstance(settings, dict) else None
        if phone_id:
            connection.execute(
                businesses.update()
                .where(businesses.c.id == business_id)
                .values(whatsapp_phone_id=phone_id)
            )

    op.create_index("ix_businesses_whatsapp_phone_id", "businesses", ["whatsapp_phone_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_businesses_whatsapp_phone_id", table_name="businesses")
    op.drop_column("businesses", "whatsapp_phone_id")
