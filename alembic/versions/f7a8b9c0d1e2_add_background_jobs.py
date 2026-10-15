"""Add persistent background retry and dead-letter state."""
from alembic import op
import sqlalchemy as sa

revision = "f7a8b9c0d1e2"
down_revision = "e6z7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "background_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=True),
        sa.Column("job_type", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("available_at", sa.DateTime(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for name, column in (("business_id", "business_id"), ("job_type", "job_type"), ("status", "status"), ("available_at", "available_at")):
        op.create_index(f"ix_background_jobs_{name}", "background_jobs", [column])


def downgrade() -> None:
    for name in ("available_at", "status", "job_type", "business_id"):
        op.drop_index(f"ix_background_jobs_{name}", table_name="background_jobs")
    op.drop_table("background_jobs")
