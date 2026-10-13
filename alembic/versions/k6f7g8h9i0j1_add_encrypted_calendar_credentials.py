"""Add encrypted storage for Google Calendar credentials."""

from alembic import op
import sqlalchemy as sa


revision = "k6f7g8h9i0j1"
down_revision = "j5e6f7g8h9i0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("businesses", sa.Column("google_calendar_credentials_encrypted", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("businesses", "google_calendar_credentials_encrypted")
