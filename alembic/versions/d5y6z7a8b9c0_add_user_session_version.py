"""Add business-user session revocation versions."""
from alembic import op
import sqlalchemy as sa

revision = "d5y6z7a8b9c0"
down_revision = "c4x5y6z7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("session_version", sa.Integer(), nullable=False, server_default="0"))
    op.alter_column("users", "session_version", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "session_version")
