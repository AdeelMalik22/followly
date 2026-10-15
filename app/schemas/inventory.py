from datetime import datetime
from pydantic import BaseModel, Field


class InventoryItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    sku: str = Field(min_length=1, max_length=80)
    category: str | None = Field(default=None, max_length=100)
    unit: str = Field(default="unit", min_length=1, max_length=30)
    quantity: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=0, ge=0)
    cost_per_unit: int | None = Field(default=None, ge=0)
    supplier: str | None = Field(default=None, max_length=160)


class InventoryItemUpdate(InventoryItemCreate):
    is_active: bool = True


class InventoryAdjustment(BaseModel):
    quantity: int = Field(gt=0)
    movement_type: str = Field(pattern="^(receive|consume|adjust)$")
    note: str | None = Field(default=None, max_length=500)


class InventoryItemResponse(BaseModel):
    id: int
    business_id: int
    name: str
    sku: str
    category: str | None
    unit: str
    quantity: int
    reorder_level: int
    cost_per_unit: int | None
    supplier: str | None
    is_active: bool
    low_stock: bool
    created_at: datetime
    updated_at: datetime


class InventoryMovementResponse(BaseModel):
    id: int
    business_id: int
    item_id: int
    movement_type: str
    quantity: int
    note: str | None
    created_by: int | None
    created_at: datetime

    class Config:
        from_attributes = True
