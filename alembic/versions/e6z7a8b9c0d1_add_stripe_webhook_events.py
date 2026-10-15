"""Persist Stripe webhook event idempotency state."""
from alembic import op
import sqlalchemy as sa

revision = "e6z7a8b9c0d1"
down_revision = "d5y6z7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stripe_webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="processed"),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_unique_constraint("uq_stripe_webhook_events_event_id", "stripe_webhook_events", ["event_id"])
    for name, column in (("business_id", "business_id"), ("event_type", "event_type"), ("received_at", "received_at")):
        op.create_index(f"ix_stripe_webhook_events_{name}", "stripe_webhook_events", [column])


def downgrade() -> None:
    for name in ("received_at", "event_type", "business_id"):
        op.drop_index(f"ix_stripe_webhook_events_{name}", table_name="stripe_webhook_events")
    op.drop_constraint("uq_stripe_webhook_events_event_id", "stripe_webhook_events", type_="unique")
    op.drop_table("stripe_webhook_events")
