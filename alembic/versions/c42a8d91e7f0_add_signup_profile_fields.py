"""Add owner name and business industry fields

Revision ID: c42a8d91e7f0
Revises: b81e4c6a2d90
"""
from alembic import op
import sqlalchemy as sa

revision = "c42a8d91e7f0"
down_revision = "b81e4c6a2d90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("businesses", sa.Column("industry", sa.String(), nullable=True))
    op.execute("UPDATE businesses SET industry = 'Dental Clinic' WHERE industry IS NULL")
    op.alter_column("businesses", "industry", nullable=False)
    op.add_column("users", sa.Column("name", sa.String(), nullable=True))
    op.execute("UPDATE users SET name = split_part(email, '@', 1) WHERE name IS NULL")
    op.alter_column("users", "name", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "name")
    op.drop_column("businesses", "industry")
