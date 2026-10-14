"""Add tenant webhook delivery metrics."""
from alembic import op
import sqlalchemy as sa

revision = "a2v3w4x5y6z7"
down_revision = "z1u2v3w4x5y6"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("businesses", sa.Column("webhook_metrics", sa.JSON(), nullable=True))

def downgrade() -> None:
    op.drop_column("businesses", "webhook_metrics")
