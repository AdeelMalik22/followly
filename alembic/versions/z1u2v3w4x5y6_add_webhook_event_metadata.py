"""Add safe webhook event metadata."""

from alembic import op
import sqlalchemy as sa


revision = "z1u2v3w4x5y6"
down_revision = "y0t1u2v3w4x5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("webhook_events", sa.Column("metadata", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("webhook_events", "metadata")
