"""Add tenant-scoped team invitations."""

from alembic import op
import sqlalchemy as sa


revision = "u6p7q8r9s0t1"
down_revision = "t5o6p7q8r9s0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "team_invitations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="staff"),
        sa.Column("token_hash", sa.String(), nullable=False, unique=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("business_id", "email", "status", name="uq_team_invites_business_email_status"),
    )
    for index_name, columns in (
        ("ix_team_invitations_id", ["id"]),
        ("ix_team_invitations_business_id", ["business_id"]),
        ("ix_team_invitations_email", ["email"]),
        ("ix_team_invitations_token_hash", ["token_hash"]),
        ("ix_team_invitations_status", ["status"]),
        ("ix_team_invitations_expires_at", ["expires_at"]),
    ):
        op.create_index(index_name, "team_invitations", columns)


def downgrade() -> None:
    for index_name in (
        "ix_team_invitations_expires_at", "ix_team_invitations_status", "ix_team_invitations_token_hash",
        "ix_team_invitations_email", "ix_team_invitations_business_id", "ix_team_invitations_id",
    ):
        op.drop_index(index_name, table_name="team_invitations")
    op.drop_table("team_invitations")
