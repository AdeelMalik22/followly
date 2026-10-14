"""Add business lifecycle, subscription, usage, and configuration audit fields."""

from alembic import op
import sqlalchemy as sa


revision = "o0j1k2l3m4n5"
down_revision = "n9i0j1k2l3m4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("businesses", sa.Column("configuration_updated_at", sa.DateTime(), nullable=True))
    op.add_column("businesses", sa.Column("configuration_updated_by", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_businesses_configuration_updated_by_users",
        "businesses",
        "users",
        ["configuration_updated_by"],
        ["id"],
    )
    op.add_column("businesses", sa.Column("lifecycle_status", sa.String(), nullable=False, server_default="onboarding"))
    op.add_column("businesses", sa.Column("lifecycle_changed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.add_column("businesses", sa.Column("plan_code", sa.String(), nullable=False, server_default="starter_trial"))
    op.add_column("businesses", sa.Column("subscription_status", sa.String(), nullable=False, server_default="trialing"))
    op.add_column("businesses", sa.Column("stripe_customer_id", sa.String(), nullable=True))
    op.add_column("businesses", sa.Column("stripe_subscription_id", sa.String(), nullable=True))
    op.add_column("businesses", sa.Column("usage_period_start", sa.DateTime(), nullable=True))
    op.add_column("businesses", sa.Column("usage_period_end", sa.DateTime(), nullable=True))
    op.add_column("businesses", sa.Column("usage_messages", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("businesses", sa.Column("usage_llm_tokens", sa.Integer(), nullable=False, server_default="0"))
    for column in ("lifecycle_status", "plan_code", "subscription_status", "usage_messages", "usage_llm_tokens"):
        op.alter_column("businesses", column, server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_businesses_configuration_updated_by_users", "businesses", type_="foreignkey")
    for column in (
        "usage_llm_tokens", "usage_messages", "usage_period_end", "usage_period_start",
        "stripe_subscription_id", "stripe_customer_id", "subscription_status", "plan_code",
        "lifecycle_changed_at", "lifecycle_status", "configuration_updated_by", "configuration_updated_at",
    ):
        op.drop_column("businesses", column)
