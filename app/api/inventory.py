from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_business, get_current_user, require_business_roles
from app.core.database import get_db
from app.models.models import Business, InventoryItem, InventoryMovement, User
from app.schemas.inventory import (
    InventoryAdjustment, InventoryItemCreate, InventoryItemResponse, InventoryItemUpdate,
    InventoryMovementResponse,
)

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


def _response(item: InventoryItem) -> InventoryItemResponse:
    return InventoryItemResponse(
        id=item.id, business_id=item.business_id, name=item.name, sku=item.sku,
        category=item.category, unit=item.unit, quantity=item.quantity,
        reorder_level=item.reorder_level, cost_per_unit=item.cost_per_unit,
        supplier=item.supplier, is_active=bool(item.is_active),
        low_stock=item.quantity <= item.reorder_level,
        created_at=item.created_at, updated_at=item.updated_at,
    )


@router.get("", response_model=list[InventoryItemResponse])
def list_items(
    search: str | None = Query(default=None),
    low_stock: bool = False,
    include_inactive: bool = False,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    query = db.query(InventoryItem).filter(InventoryItem.business_id == business.id)
    if not include_inactive:
        query = query.filter(InventoryItem.is_active == 1)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter((InventoryItem.name.ilike(term)) | (InventoryItem.sku.ilike(term)))
    items = query.order_by(InventoryItem.name.asc()).all()
    if low_stock:
        items = [item for item in items if item.quantity <= item.reorder_level]
    return [_response(item) for item in items]


@router.post("", response_model=InventoryItemResponse)
def create_item(
    payload: InventoryItemCreate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
    _user: User = Depends(require_business_roles("owner", "admin", "staff")),
):
    if db.query(InventoryItem).filter(InventoryItem.business_id == business.id, InventoryItem.sku == payload.sku).first():
        raise HTTPException(status_code=409, detail="An inventory item with this SKU already exists")
    item = InventoryItem(business_id=business.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return _response(item)


@router.get("/summary/low-stock", response_model=list[InventoryItemResponse])
def low_stock_summary(business: Business = Depends(get_current_business), db: Session = Depends(get_db)):
    items = db.query(InventoryItem).filter(
        InventoryItem.business_id == business.id,
        InventoryItem.is_active == 1,
    ).order_by(InventoryItem.quantity.asc()).all()
    return [_response(item) for item in items if item.quantity <= item.reorder_level]


@router.get("/{item_id}", response_model=InventoryItemResponse)
def get_item(item_id: int, business: Business = Depends(get_current_business), db: Session = Depends(get_db)):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id, InventoryItem.business_id == business.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return _response(item)


@router.put("/{item_id}", response_model=InventoryItemResponse)
def update_item(
    item_id: int,
    payload: InventoryItemUpdate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
    _user: User = Depends(require_business_roles("owner", "admin", "staff")),
):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id, InventoryItem.business_id == business.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    duplicate = db.query(InventoryItem).filter(InventoryItem.business_id == business.id, InventoryItem.sku == payload.sku, InventoryItem.id != item_id).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="An inventory item with this SKU already exists")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return _response(item)


@router.post("/{item_id}/adjust", response_model=InventoryItemResponse)
def adjust_item(
    item_id: int,
    payload: InventoryAdjustment,
    business: Business = Depends(get_current_business),
    user: User = Depends(require_business_roles("owner", "admin", "staff")),
    db: Session = Depends(get_db),
):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id, InventoryItem.business_id == business.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    if payload.movement_type == "consume" and item.quantity < payload.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock for this adjustment")
    item.quantity += payload.quantity if payload.movement_type == "receive" else -payload.quantity if payload.movement_type == "consume" else payload.quantity
    movement = InventoryMovement(business_id=business.id, item_id=item.id, created_by=user.id, **payload.model_dump())
    db.add(movement)
    db.commit()
    db.refresh(item)
    return _response(item)


@router.get("/{item_id}/movements", response_model=list[InventoryMovementResponse])
def list_movements(item_id: int, business: Business = Depends(get_current_business), db: Session = Depends(get_db)):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id, InventoryItem.business_id == business.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return db.query(InventoryMovement).filter(
        InventoryMovement.item_id == item_id, InventoryMovement.business_id == business.id
    ).order_by(InventoryMovement.created_at.desc()).all()


@router.delete("/{item_id}")
def deactivate_item(
    item_id: int,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
    _user: User = Depends(require_business_roles("owner", "admin")),
):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id, InventoryItem.business_id == business.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    item.is_active = 0
    db.commit()
    return {"status": "deactivated"}
