"""Add knowledge source metadata and deletion lifecycle."""

from alembic import op
import sqlalchemy as sa


revision = "q2l3m4n5o6p7"
down_revision = "p1k2l3m4n5o6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("knowledge_base", sa.Column("source_name", sa.String(), nullable=True))
    op.add_column("knowledge_base", sa.Column("source_uri", sa.String(), nullable=True))
    op.add_column("knowledge_base", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("knowledge_base", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.create_index("ix_knowledge_base_deleted_at", "knowledge_base", ["deleted_at"])
    op.alter_column("knowledge_base", "version", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_knowledge_base_deleted_at", table_name="knowledge_base")
    for column in ("deleted_at", "version", "source_uri", "source_name"):
        op.drop_column("knowledge_base", column)
