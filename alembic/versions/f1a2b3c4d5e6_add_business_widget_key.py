"""Promote the business widget key to an indexed column."""

from alembic import op
import sqlalchemy as sa


revision = "f1a2b3c4d5e6"
down_revision = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("businesses", sa.Column("widget_key", sa.String(), nullable=True))

    businesses = sa.table(
        "businesses",
        sa.column("id", sa.Integer()),
        sa.column("settings", sa.JSON()),
        sa.column("widget_key", sa.String()),
    )
    connection = op.get_bind()
    rows = connection.execute(sa.select(businesses.c.id, businesses.c.settings)).fetchall()
    for business_id, settings in rows:
        widget_key = (settings or {}).get("widget_key") if isinstance(settings, dict) else None
        if widget_key:
            connection.execute(
                businesses.update()
                .where(businesses.c.id == business_id)
                .values(widget_key=widget_key)
            )

    op.create_index("ix_businesses_widget_key", "businesses", ["widget_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_businesses_widget_key", table_name="businesses")
    op.drop_column("businesses", "widget_key")
