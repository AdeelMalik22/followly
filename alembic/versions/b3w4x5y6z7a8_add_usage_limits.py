"""Add configurable tenant usage limits."""
from alembic import op
import sqlalchemy as sa

revision = "b3w4x5y6z7a8"
down_revision = "a2v3w4x5y6z7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("businesses", sa.Column("usage_limits", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("businesses", "usage_limits")
