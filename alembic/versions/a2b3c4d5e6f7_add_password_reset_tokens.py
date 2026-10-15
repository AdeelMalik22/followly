"""Add password recovery tokens."""

from alembic import op
import sqlalchemy as sa

revision = "a2b3c4d5e6f7"
down_revision = "z1u2v3w4x5y6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("token_hash", name="uq_password_reset_tokens_token_hash"),
    )
    for name in ("user_id", "token_hash", "expires_at"):
        op.create_index(f"ix_password_reset_tokens_{name}", "password_reset_tokens", [name])


def downgrade() -> None:
    for name in ("user_id", "token_hash", "expires_at"):
        op.drop_index(f"ix_password_reset_tokens_{name}", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
