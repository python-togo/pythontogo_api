from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Annotated
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone
from json import dumps, loads
from psycopg.rows import dict_row

from app.database.connection import get_db_connection, get_redis_client
from app.database.orm import select
from app.schemas.shop import CategorySummary, ProductSummary, ProductDetail, VariantSummary, CartItem, CartItemUpdate, CartLineDetail, CartSummary, CheckoutPayload, OrderSummary, OrderDetail, OrderItemSummary
from app.core.security import get_current_user
from app.schemas.models import AuthenticatedUser
from app.utils.responses import success
from app.utils.pagination import paginate

api_router = APIRouter(tags=["shop"])

_CART_TTL = 7 * 24 * 3600


def _cart_key(user_id) -> str:
    return f"PYTOGO_CART:{user_id}"


async def _get_raw_cart(redis, user_id: UUID) -> dict:
    raw = await redis.get(_cart_key(user_id))
    if not raw:
        return {"items": {}, "coupon_code": None}
    return loads(raw)


async def _save_cart(redis, user_id: UUID, cart: dict):
    await redis.set(_cart_key(user_id), dumps(cart), ex=_CART_TTL)


async def _build_cart_summary(cart: dict, db) -> CartSummary:
    lines: list[CartLineDetail] = []
    for variant_id, qty in cart["items"].items():
        rows = await select(db, "product_variants", filter={"id": variant_id})
        if not rows or not rows[0]["is_active"]:
            continue
        v = rows[0]
        product_rows = await select(db, "products", filter={"id": str(v["product_id"])})
        if not product_rows or not product_rows[0]["is_active"]:
            continue
        price = Decimal(str(v["price_override"] or product_rows[0]["base_price"]))
        lines.append(CartLineDetail(
            variant_id=variant_id, quantity=qty, sku=v["sku"],
            name=f"{product_rows[0]['name']} — {v['name']}",
            unit_price=price, subtotal=price * qty,
        ))

    subtotal = sum(l.subtotal for l in lines)
    coupon_code = cart.get("coupon_code")
    return CartSummary(items=lines, coupon_code=coupon_code, subtotal=subtotal, discount_amount=Decimal("0.00"), total=subtotal)


# ── Public ────────────────────────────────────────────────────────────────────

@api_router.get("/categories")
async def list_categories(db=Depends(get_db_connection)):
    return success(await select(db, "categories", filter={"is_active": True}) or [])


@api_router.get("/categories/{category_id}")
async def get_category(category_id: UUID, db=Depends(get_db_connection)):
    rows = await select(db, "categories", filter={"id": str(category_id), "is_active": True})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return success(CategorySummary(**rows[0]))


@api_router.get("/products")
async def list_products(
    event_id: UUID | None = Query(default=None),
    category_id: UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
):
    conditions = ["is_active = true"]
    params: list = []
    if event_id:
        conditions.append("event_id = %s")
        params.append(str(event_id))
    if category_id:
        conditions.append("category_id = %s")
        params.append(str(category_id))
    sql = f"SELECT * FROM products WHERE {' AND '.join(conditions)} ORDER BY created_at DESC"
    rows, total = await paginate(db, sql, tuple(params), page, per_page)
    return success(rows, total=total, page=page, per_page=per_page)


@api_router.get("/products/{product_id}")
async def get_product(product_id: UUID, db=Depends(get_db_connection)):
    rows = await select(db, "products", filter={"id": str(product_id), "is_active": True})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    variants = await select(db, "product_variants", filter={"product_id": str(product_id), "is_active": True}) or []
    product = ProductDetail(**rows[0])
    product.variants = [VariantSummary(**v) for v in variants]
    return success(product)


# ── Cart ──────────────────────────────────────────────────────────────────────

@api_router.get("/cart")
async def get_cart(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db=Depends(get_db_connection),
    redis=Depends(get_redis_client),
):
    cart = await _get_raw_cart(redis, current_user.id)
    return success(await _build_cart_summary(cart, db))


@api_router.post("/cart/items", status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    payload: CartItem,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db=Depends(get_db_connection),
    redis=Depends(get_redis_client),
):
    variant_rows = await select(db, "product_variants", filter={"id": str(payload.variant_id), "is_active": True})
    if not variant_rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found or inactive")

    variant = variant_rows[0]
    cart = await _get_raw_cart(redis, current_user.id)
    new_qty = cart["items"].get(str(payload.variant_id), 0) + payload.quantity

    if new_qty > variant["stock_quantity"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stock insuffisant — disponible : {variant['stock_quantity']}")

    cart["items"][str(payload.variant_id)] = new_qty
    await _save_cart(redis, current_user.id, cart)
    return success(await _build_cart_summary(cart, db), code=201)


@api_router.put("/cart/items/{variant_id}")
async def update_cart_item(
    variant_id: UUID,
    payload: CartItemUpdate,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db=Depends(get_db_connection),
    redis=Depends(get_redis_client),
):
    cart = await _get_raw_cart(redis, current_user.id)
    if str(variant_id) not in cart["items"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not in cart")
    variant_rows = await select(db, "product_variants", filter={"id": str(variant_id)})
    if not variant_rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
    if payload.quantity > variant_rows[0]["stock_quantity"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stock insuffisant — disponible : {variant_rows[0]['stock_quantity']}")
    cart["items"][str(variant_id)] = payload.quantity
    await _save_cart(redis, current_user.id, cart)
    return success(await _build_cart_summary(cart, db))


@api_router.delete("/cart/items/{variant_id}")
async def remove_cart_item(
    variant_id: UUID,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db=Depends(get_db_connection),
    redis=Depends(get_redis_client),
):
    cart = await _get_raw_cart(redis, current_user.id)
    cart["items"].pop(str(variant_id), None)
    await _save_cart(redis, current_user.id, cart)
    return success(await _build_cart_summary(cart, db))


@api_router.delete("/cart")
async def clear_cart(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    redis=Depends(get_redis_client),
):
    await redis.delete(_cart_key(current_user.id))
    return success({"message": "Cart cleared"})


# ── Checkout ──────────────────────────────────────────────────────────────────

@api_router.post("/cart/checkout", status_code=status.HTTP_201_CREATED)
async def checkout(
    payload: CheckoutPayload,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db=Depends(get_db_connection),
    redis=Depends(get_redis_client),
):
    cart = await _get_raw_cart(redis, current_user.id)
    if not cart["items"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    coupon_code = payload.coupon_code or cart.get("coupon_code")
    coupon = None
    discount_amount = Decimal("0.00")

    if coupon_code:
        coupon_rows = await select(db, "coupons", filter={"code": coupon_code, "is_active": True})
        if not coupon_rows:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon invalide ou inactif")
        coupon = coupon_rows[0]
        now = datetime.now(timezone.utc)
        if coupon["expires_at"] and coupon["expires_at"] < now:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon expiré")
        if coupon["max_uses"] and coupon["uses_count"] >= coupon["max_uses"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon épuisé")

    items_data = []
    subtotal = Decimal("0.00")

    for variant_id, qty in cart["items"].items():
        variant_rows = await select(db, "product_variants", filter={"id": variant_id, "is_active": True})
        if not variant_rows:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Variante {variant_id} introuvable ou désactivée")
        v = variant_rows[0]
        if not await select(db, "products", filter={"id": str(v["product_id"]), "is_active": True}):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Le produit lié à la variante {variant_id} est désactivé")
        if v["stock_quantity"] < qty:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stock insuffisant pour {v['sku']} — disponible : {v['stock_quantity']}")
        product_rows = await select(db, "products", filter={"id": str(v["product_id"])})
        unit_price = Decimal(str(v["price_override"] or product_rows[0]["base_price"]))
        subtotal += unit_price * qty
        items_data.append({"variant_id": variant_id, "quantity": qty, "unit_price": unit_price})

    if coupon:
        if coupon["type"] == "percentage":
            discount_amount = (subtotal * Decimal(str(coupon["value"])) / 100).quantize(Decimal("0.01"))
        else:
            discount_amount = min(Decimal(str(coupon["value"])), subtotal)

    total_amount = subtotal - discount_amount

    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "INSERT INTO shop_orders (event_id, user_id, coupon_id, status, total_amount, discount_amount, shipping_address) "
            "VALUES (%s, %s, %s, 'pending', %s, %s, %s) RETURNING *",
            (str(payload.event_id), str(current_user.id), str(coupon["id"]) if coupon else None,
             str(total_amount), str(discount_amount), dumps(payload.shipping_address)),
        )
        order_row = await cur.fetchone()

        for item in items_data:
            await cur.execute(
                "INSERT INTO order_items (order_id, product_variant_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                (str(order_row["id"]), item["variant_id"], item["quantity"], str(item["unit_price"])),
            )
            await cur.execute(
                "UPDATE product_variants SET stock_quantity = stock_quantity - %s WHERE id = %s",
                (item["quantity"], item["variant_id"]),
            )
        if coupon:
            await cur.execute("UPDATE coupons SET uses_count = uses_count + 1 WHERE id = %s", (str(coupon["id"]),))

    await db.commit()
    await redis.delete(_cart_key(current_user.id))
    return success(OrderSummary(**order_row), code=201)


# ── My orders ─────────────────────────────────────────────────────────────────

@api_router.get("/orders/me")
async def my_orders(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db_connection),
):
    rows, total = await paginate(
        db,
        "SELECT * FROM shop_orders WHERE user_id = %s ORDER BY created_at DESC",
        (str(current_user.id),),
        page, per_page,
    )
    return success(rows, total=total, page=page, per_page=per_page)


@api_router.get("/orders/me/{order_id}")
async def my_order_detail(order_id: UUID, current_user: Annotated[AuthenticatedUser, Depends(get_current_user)], db=Depends(get_db_connection)):
    rows = await select(db, "shop_orders", filter={"id": str(order_id), "user_id": str(current_user.id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    items = await select(db, "order_items", filter={"order_id": str(order_id)}) or []
    order = OrderDetail(**rows[0])
    order.items = [OrderItemSummary(**i) for i in items]
    return success(order)
