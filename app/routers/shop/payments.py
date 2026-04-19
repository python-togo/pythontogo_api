from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.database.connection import get_db_connection
from app.database.orm import select
from app.schemas.shop import PaymentSummary
from app.core.security import require_admin

api_router = APIRouter(prefix="/payments", tags=["shop-payments"])


@api_router.get("", response_model=list[PaymentSummary])
async def list_payments(db=Depends(get_db_connection), _=Depends(require_admin)):
    return await select(db, "shop_payments") or []


@api_router.get("/{payment_id}", response_model=PaymentSummary)
async def get_payment(payment_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "shop_payments", filter={"id": str(payment_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return PaymentSummary(**rows[0])
