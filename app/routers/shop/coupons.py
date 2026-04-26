from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID

from app.database.connection import get_db_connection
from app.database.orm import select, insert, update, delete
from app.schemas.shop import CouponCreate, CouponUpdate, CouponSummary
from app.core.security import require_admin
from app.utils.responses import success
from app.utils.pagination import paginate

api_router = APIRouter(prefix="/coupons", tags=["shop-coupons"])


@api_router.get("")
async def list_coupons(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    rows, total = await paginate(
        db,
        "SELECT * FROM coupons ORDER BY created_at DESC",
        (),
        page, per_page,
    )
    return success(rows, total=total, page=page, per_page=per_page)


@api_router.post("", status_code=status.HTTP_201_CREATED)
async def create_coupon(payload: CouponCreate, db=Depends(get_db_connection), _=Depends(require_admin)):
    if await select(db, "coupons", filter={"code": payload.code}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Coupon code already exists")
    data = {k: str(v) if v is not None and not isinstance(v, (bool, int, float)) else v for k, v in payload.model_dump().items()}
    data = {k: v for k, v in data.items() if v is not None}
    data["uses_count"] = 0
    await insert(db, "coupons", data)
    rows = await select(db, "coupons", filter={"code": payload.code})
    return success(CouponSummary(**rows[0]), code=201)


@api_router.put("/{coupon_id}")
async def update_coupon(coupon_id: UUID, payload: CouponUpdate, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "coupons", filter={"id": str(coupon_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")
    await update(db, "coupons", payload.model_dump(exclude_none=True), {"id": str(coupon_id)})
    rows = await select(db, "coupons", filter={"id": str(coupon_id)})
    return success(CouponSummary(**rows[0]))


@api_router.delete("/{coupon_id}")
async def delete_coupon(coupon_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "coupons", filter={"id": str(coupon_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")
    await delete(db, "coupons", {"id": str(coupon_id)})
    return success({"message": "Coupon deleted"})
