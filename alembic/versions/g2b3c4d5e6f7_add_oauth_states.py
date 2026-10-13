"""Add one-time OAuth state storage."""

from alembic import op
import sqlalchemy as sa


revision = "g2b3c4d5e6f7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "oauth_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("state_hash", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_oauth_states_id", "oauth_states", ["id"])
    op.create_index("ix_oauth_states_business_id", "oauth_states", ["business_id"])
    op.create_index("ix_oauth_states_state_hash", "oauth_states", ["state_hash"], unique=True)
    op.create_index("ix_oauth_states_expires_at", "oauth_states", ["expires_at"])


def downgrade() -> None:
    for index_name in (
        "ix_oauth_states_expires_at",
        "ix_oauth_states_state_hash",
        "ix_oauth_states_business_id",
        "ix_oauth_states_id",
    ):
        op.drop_index(index_name, table_name="oauth_states")
    op.drop_table("oauth_states")
