"""Add tenant tool usage counter."""

from alembic import op
import sqlalchemy as sa


revision = "r3m4n5o6p7q8"
down_revision = "q2l3m4n5o6p7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("businesses", sa.Column("usage_tool_calls", sa.Integer(), nullable=False, server_default="0"))
    op.alter_column("businesses", "usage_tool_calls", server_default=None)


def downgrade() -> None:
    op.drop_column("businesses", "usage_tool_calls")
