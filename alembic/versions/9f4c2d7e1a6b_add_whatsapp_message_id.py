"""Add WhatsApp message ID for webhook idempotency

Revision ID: 9f4c2d7e1a6b
Revises: 7c8b9a35cdfb
Create Date: 2026-08-27
"""

from alembic import op
import sqlalchemy as sa


revision = "9f4c2d7e1a6b"
down_revision = "7c8b9a35cdfb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("whatsapp_message_id", sa.String(), nullable=True))
    op.create_index(
        "ix_messages_whatsapp_message_id",
        "messages",
        ["whatsapp_message_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_messages_whatsapp_message_id", table_name="messages")
    op.drop_column("messages", "whatsapp_message_id")
