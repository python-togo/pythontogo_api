from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from datetime import datetime, timezone

from app.database.connection import get_db_connection
from app.database.orm import select, update
from app.schemas.models import UserSummary
from app.schemas.shop import OrderSummary
from app.core.security import require_admin

api_router = APIRouter(prefix="/customers", tags=["shop-customers"])


@api_router.get("", response_model=list[UserSummary])
async def list_customers(db=Depends(get_db_connection), _=Depends(require_admin)):
    return await select(db, "users") or []


@api_router.get("/{customer_id}", response_model=UserSummary)
async def get_customer(customer_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "users", filter={"id": str(customer_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return UserSummary(**rows[0])


@api_router.get("/{customer_id}/orders", response_model=list[OrderSummary])
async def get_customer_orders(customer_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "users", filter={"id": str(customer_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return await select(db, "shop_orders", filter={"user_id": str(customer_id)}) or []


@api_router.patch("/{customer_id}/toggle", response_model=UserSummary)
async def toggle_customer(customer_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "users", filter={"id": str(customer_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    new_status = not rows[0]["is_active"]
    await update(db, "users", {"is_active": new_status, "updated_at": datetime.now(timezone.utc)}, {"id": str(customer_id)})
    rows = await select(db, "users", filter={"id": str(customer_id)})
    return UserSummary(**rows[0])
