"""Add appointment status history auditing."""

from alembic import op
import sqlalchemy as sa


revision = "l7g8h9i0j1k2"
down_revision = "k6f7g8h9i0j1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "appointment_status_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("appointment_id", sa.Integer(), sa.ForeignKey("appointments.id"), nullable=False),
        sa.Column("previous_status", sa.String(), nullable=False),
        sa.Column("new_status", sa.String(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_appointment_status_history_id", "appointment_status_history", ["id"])
    op.create_index("ix_appointment_status_history_business_id", "appointment_status_history", ["business_id"])
    op.create_index("ix_appointment_status_history_appointment_id", "appointment_status_history", ["appointment_id"])
    op.create_index("ix_appointment_status_history_changed_at", "appointment_status_history", ["changed_at"])


def downgrade() -> None:
    for index_name in (
        "ix_appointment_status_history_changed_at",
        "ix_appointment_status_history_appointment_id",
        "ix_appointment_status_history_business_id",
        "ix_appointment_status_history_id",
    ):
        op.drop_index(index_name, table_name="appointment_status_history")
    op.drop_table("appointment_status_history")
