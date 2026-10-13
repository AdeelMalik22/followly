"""add customer Google identity uniqueness

Revision ID: e3f4a5b6c7d8
Revises: d5e7f8a9b0c1
"""

from alembic import op


revision = "e3f4a5b6c7d8"
down_revision = "d5e7f8a9b0c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_customers_business_google_id",
        "customers",
        ["business_id", "google_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_customers_business_google_id", "customers", type_="unique")
