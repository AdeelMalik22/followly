"""Add immutable structured configuration history."""
from alembic import op
import sqlalchemy as sa

revision = "c4x5y6z7a8b9"
down_revision = "b3w4x5y6z7a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "configuration_audits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("changed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_configuration_audits_business_id", "configuration_audits", ["business_id"])
    op.create_index("ix_configuration_audits_changed_by", "configuration_audits", ["changed_by"])
    op.create_index("ix_configuration_audits_created_at", "configuration_audits", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_configuration_audits_created_at", table_name="configuration_audits")
    op.drop_index("ix_configuration_audits_changed_by", table_name="configuration_audits")
    op.drop_index("ix_configuration_audits_business_id", table_name="configuration_audits")
    op.drop_table("configuration_audits")
