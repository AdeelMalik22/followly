"""Add persistent tool call audit records

Revision ID: b81e4c6a2d90
Revises: 9f4c2d7e1a6b
"""

from alembic import op
import sqlalchemy as sa


revision = "b81e4c6a2d90"
down_revision = "9f4c2d7e1a6b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tool_call_audits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("success", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tool_call_audits_id", "tool_call_audits", ["id"], unique=False)
    op.create_index("ix_tool_call_audits_conversation_id", "tool_call_audits", ["conversation_id"], unique=False)
    op.create_index("ix_tool_call_audits_created_at", "tool_call_audits", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tool_call_audits_created_at", table_name="tool_call_audits")
    op.drop_index("ix_tool_call_audits_conversation_id", table_name="tool_call_audits")
    op.drop_index("ix_tool_call_audits_id", table_name="tool_call_audits")
    op.drop_table("tool_call_audits")
