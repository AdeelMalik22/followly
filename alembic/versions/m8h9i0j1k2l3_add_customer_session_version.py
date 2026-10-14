"""Add customer session version for token revocation."""

from alembic import op
import sqlalchemy as sa


revision = "m8h9i0j1k2l3"
down_revision = "l7g8h9i0j1k2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column("session_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("customers", "session_version", server_default=None)


def downgrade() -> None:
    op.drop_column("customers", "session_version")
