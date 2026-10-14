"""Add tenant knowledge document sources."""

from alembic import op
import sqlalchemy as sa


revision = "v7q8r9s0t1u2"
down_revision = "u6p7q8r9s0t1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False, server_default="document"),
        sa.Column("uri", sa.String(), nullable=True),
        sa.Column("mime_type", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("visibility", sa.String(), nullable=False, server_default="active"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.add_column("knowledge_base", sa.Column("source_id", sa.Integer(), nullable=True))
    op.add_column("knowledge_base", sa.Column("visibility", sa.String(), nullable=False, server_default="active"))
    op.create_foreign_key("fk_knowledge_base_source_id", "knowledge_base", "knowledge_sources", ["source_id"], ["id"])
    for table, names in (("knowledge_sources", ("id", "business_id", "status", "visibility")), ("knowledge_base", ("source_id", "visibility"))):
        for name in names:
            op.create_index(f"ix_{table}_{name}", table, [name])
    op.alter_column("knowledge_sources", "source_type", server_default=None)
    op.alter_column("knowledge_sources", "status", server_default=None)
    op.alter_column("knowledge_sources", "visibility", server_default=None)
    op.alter_column("knowledge_sources", "version", server_default=None)
    op.alter_column("knowledge_base", "visibility", server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_knowledge_base_source_id", "knowledge_base", type_="foreignkey")
    for name in ("ix_knowledge_base_visibility", "ix_knowledge_base_source_id"):
        op.drop_index(name, table_name="knowledge_base")
    op.drop_column("knowledge_base", "visibility")
    op.drop_column("knowledge_base", "source_id")
    for name in ("ix_knowledge_sources_visibility", "ix_knowledge_sources_status", "ix_knowledge_sources_business_id", "ix_knowledge_sources_id"):
        op.drop_index(name, table_name="knowledge_sources")
    op.drop_table("knowledge_sources")
