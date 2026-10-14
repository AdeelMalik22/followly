"""Add validated tenant configuration storage."""

from alembic import op
import sqlalchemy as sa


revision = "n9i0j1k2l3m4"
down_revision = "m8h9i0j1k2l3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("businesses", sa.Column("configuration", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("businesses", "configuration")
