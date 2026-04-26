from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
from datetime import datetime, timezone

from app.database.connection import get_db_connection
from app.database.orm import select, update
from app.schemas.models import UserSummary
from app.schemas.shop import OrderSummary
from app.core.security import require_admin
from app.utils.responses import success
from app.utils.pagination import paginate

api_router = APIRouter(prefix="/customers", tags=["shop-customers"])


@api_router.get("")
async def list_customers(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    rows, total = await paginate(
        db,
        "SELECT * FROM users ORDER BY created_at DESC",
        (),
        page, per_page,
    )
    return success(rows, total=total, page=page, per_page=per_page)


@api_router.get("/{customer_id}")
async def get_customer(customer_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "users", filter={"id": str(customer_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return success(UserSummary(**rows[0]))


@api_router.get("/{customer_id}/orders")
async def get_customer_orders(customer_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "users", filter={"id": str(customer_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return success(await select(db, "shop_orders", filter={"user_id": str(customer_id)}) or [])


@api_router.patch("/{customer_id}/toggle")
async def toggle_customer(customer_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "users", filter={"id": str(customer_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    await update(db, "users", {"is_active": not rows[0]["is_active"], "updated_at": datetime.now(timezone.utc)}, {"id": str(customer_id)})
    rows = await select(db, "users", filter={"id": str(customer_id)})
    return success(UserSummary(**rows[0]))
