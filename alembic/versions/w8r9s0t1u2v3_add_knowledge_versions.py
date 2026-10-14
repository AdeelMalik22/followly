"""Add immutable knowledge version snapshots."""

from alembic import op
import sqlalchemy as sa


revision = "w8r9s0t1u2v3"
down_revision = "v7q8r9s0t1u2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("entry_id", sa.Integer(), sa.ForeignKey("knowledge_base.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("question", sa.String(), nullable=True),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for name, table, column in (
        ("ix_knowledge_versions_id", "knowledge_versions", "id"),
        ("ix_knowledge_versions_business_id", "knowledge_versions", "business_id"),
        ("ix_knowledge_versions_entry_id", "knowledge_versions", "entry_id"),
    ):
        op.create_index(name, table, [column])


def downgrade() -> None:
    for name in ("ix_knowledge_versions_entry_id", "ix_knowledge_versions_business_id", "ix_knowledge_versions_id"):
        op.drop_index(name, table_name="knowledge_versions")
    op.drop_table("knowledge_versions")
