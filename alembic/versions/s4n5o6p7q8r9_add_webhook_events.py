"""Persist tenant-scoped webhook idempotency events."""

from alembic import op
import sqlalchemy as sa


revision = "s4n5o6p7q8r9"
down_revision = "r3m4n5o6p7q8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="processing"),
        sa.Column("received_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.UniqueConstraint("business_id", "event_id", name="uq_webhook_events_business_event"),
    )
    op.create_index("ix_webhook_events_id", "webhook_events", ["id"])
    op.create_index("ix_webhook_events_business_id", "webhook_events", ["business_id"])
    op.create_index("ix_webhook_events_status", "webhook_events", ["status"])


def downgrade() -> None:
    for index_name in ("ix_webhook_events_status", "ix_webhook_events_business_id", "ix_webhook_events_id"):
        op.drop_index(index_name, table_name="webhook_events")
    op.drop_table("webhook_events")
