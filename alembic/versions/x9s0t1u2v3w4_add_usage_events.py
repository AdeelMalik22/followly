"""Add detailed tenant usage events."""

from alembic import op
import sqlalchemy as sa


revision = "x9s0t1u2v3w4"
down_revision = "w8r9s0t1u2v3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usage_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("llm_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tool_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for name, column in (("id", "id"), ("business_id", "business_id"), ("event_type", "event_type"), ("created_at", "created_at")):
        op.create_index(f"ix_usage_events_{name}", "usage_events", [column])


def downgrade() -> None:
    for name in ("created_at", "event_type", "business_id", "id"):
        op.drop_index(f"ix_usage_events_{name}", table_name="usage_events")
    op.drop_table("usage_events")
