from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
from datetime import datetime, timezone
from psycopg.rows import dict_row

from app.database.connection import get_db_connection
from app.database.orm import select, update
from app.schemas.shop import OrderSummary, OrderDetail, OrderStatusUpdate, OrderItemSummary, OrderStatus
from app.core.security import require_admin
from app.utils.responses import success

api_router = APIRouter(prefix="/orders", tags=["shop-orders"])


@api_router.get("")
async def list_orders(
    event_id: UUID | None = Query(default=None),
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    user_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db=Depends(get_db_connection),
    _=Depends(require_admin),
):
    conditions, values = [], []
    if event_id:
        conditions.append("event_id = %s"); values.append(str(event_id))
    if status_filter:
        conditions.append("status = %s"); values.append(status_filter.value)
    if user_id:
        conditions.append("user_id = %s"); values.append(str(user_id))

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    values += [limit, offset]

    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"SELECT * FROM shop_orders {where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
            tuple(values),
        )
        rows = await cur.fetchall()
    return success(rows or [], total=len(rows))


@api_router.get("/{order_id}")
async def get_order(order_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "shop_orders", filter={"id": str(order_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    items = await select(db, "order_items", filter={"order_id": str(order_id)}) or []
    order = OrderDetail(**rows[0])
    order.items = [OrderItemSummary(**i) for i in items]
    return success(order)


@api_router.patch("/{order_id}/status")
async def update_order_status(order_id: UUID, payload: OrderStatusUpdate, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "shop_orders", filter={"id": str(order_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    await update(db, "shop_orders", {"status": payload.status.value, "updated_at": datetime.now(timezone.utc)}, {"id": str(order_id)})
    rows = await select(db, "shop_orders", filter={"id": str(order_id)})
    return success(OrderSummary(**rows[0]))
