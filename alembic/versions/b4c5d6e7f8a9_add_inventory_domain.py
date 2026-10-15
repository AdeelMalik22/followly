"""Add tenant-scoped inventory items and stock movements."""

from alembic import op
import sqlalchemy as sa

revision = "b4c5d6e7f8a9"
down_revision = ("a2b3c4d5e6f7", "f7a8b9c0d1e2")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("sku", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("unit", sa.String(), nullable=False, server_default="unit"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_per_unit", sa.Integer(), nullable=True),
        sa.Column("supplier", sa.String(), nullable=True),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("business_id", "sku", name="uq_inventory_items_business_sku"),
    )
    op.create_index("ix_inventory_items_business_id", "inventory_items", ["business_id"])
    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("inventory_items.id"), nullable=False),
        sa.Column("movement_type", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for name in ("business_id", "item_id", "created_by", "created_at"):
        op.create_index(f"ix_inventory_movements_{name}", "inventory_movements", [name])


def downgrade() -> None:
    for name in ("business_id", "item_id", "created_by", "created_at"):
        op.drop_index(f"ix_inventory_movements_{name}", table_name="inventory_movements")
    op.drop_table("inventory_movements")
    op.drop_index("ix_inventory_items_business_id", table_name="inventory_items")
    op.drop_table("inventory_items")
