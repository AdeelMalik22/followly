"""Add business-scoped customer identities for returning chat users."""

from alembic import op
import sqlalchemy as sa


revision = "d5e7f8a9b0c1"
down_revision = "c42a8d91e7f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("google_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_customers_id", "customers", ["id"])
    op.create_index("ix_customers_business_id", "customers", ["business_id"])
    op.create_index("ix_customers_email", "customers", ["email"])
    op.create_index("ix_customers_google_id", "customers", ["google_id"])
    op.add_column("leads", sa.Column("customer_id", sa.Integer(), nullable=True))
    op.create_index("ix_leads_customer_id", "leads", ["customer_id"])
    op.create_foreign_key("fk_leads_customer_id", "leads", "customers", ["customer_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_leads_customer_id", "leads", type_="foreignkey")
    op.drop_index("ix_leads_customer_id", table_name="leads")
    op.drop_column("leads", "customer_id")
    for index_name in ("ix_customers_google_id", "ix_customers_email", "ix_customers_business_id", "ix_customers_id"):
        op.drop_index(index_name, table_name="customers")
    op.drop_table("customers")
