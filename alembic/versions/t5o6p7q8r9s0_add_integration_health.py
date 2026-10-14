"""Add tenant integration health state."""

from alembic import op
import sqlalchemy as sa


revision = "t5o6p7q8r9s0"
down_revision = "s4n5o6p7q8r9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("businesses", sa.Column("integration_health", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("businesses", "integration_health")
