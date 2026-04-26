from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID

from app.database.connection import get_db_connection
from app.database.orm import select
from app.schemas.shop import PaymentSummary
from app.core.security import require_admin
from app.utils.responses import success
from app.utils.pagination import paginate

api_router = APIRouter(prefix="/payments", tags=["shop-payments"])


@api_router.get("")
async def list_payments(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    rows, total = await paginate(
        db,
        "SELECT * FROM shop_payments ORDER BY created_at DESC",
        (),
        page, per_page,
    )
    return success(rows, total=total, page=page, per_page=per_page)


@api_router.get("/{payment_id}")
async def get_payment(payment_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "shop_payments", filter={"id": str(payment_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return success(PaymentSummary(**rows[0]))
