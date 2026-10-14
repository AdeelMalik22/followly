"""Add webhook retry accounting."""

from alembic import op
import sqlalchemy as sa


revision = "y0t1u2v3w4x5"
down_revision = "x9s0t1u2v3w4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("webhook_events", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))
    op.alter_column("webhook_events", "retry_count", server_default=None)


def downgrade() -> None:
    op.drop_column("webhook_events", "retry_count")
