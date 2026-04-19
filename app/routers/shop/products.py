from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from datetime import datetime, timezone

from app.database.connection import get_db_connection
from app.database.orm import select, insert, update, delete
from app.schemas.shop import (
    ProductCreate, ProductUpdate, ProductSummary,
    VariantCreate, VariantUpdate, VariantSummary,
)
from app.core.security import require_admin

api_router = APIRouter(prefix="/products", tags=["shop-products"])


@api_router.get("", response_model=list[ProductSummary])
async def list_products(db=Depends(get_db_connection), _=Depends(require_admin)):
    return await select(db, "products") or []


@api_router.post("", response_model=ProductSummary, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, db=Depends(get_db_connection), _=Depends(require_admin)):
    existing = await select(db, "products", filter={"slug": payload.slug})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already used")

    data = {k: str(v) if v is not None else None for k, v in payload.model_dump().items()}
    data = {k: v for k, v in data.items() if v is not None}
    await insert(db, "products", data)

    rows = await select(db, "products", filter={"slug": payload.slug})
    return ProductSummary(**rows[0])


@api_router.get("/{product_id}", response_model=ProductSummary)
async def get_product(product_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "products", filter={"id": str(product_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductSummary(**rows[0])


@api_router.put("/{product_id}", response_model=ProductSummary)
async def update_product(product_id: UUID, payload: ProductUpdate, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "products", filter={"id": str(product_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    await update(db, "products", payload.model_dump(exclude_none=True), {"id": str(product_id)})
    rows = await select(db, "products", filter={"id": str(product_id)})
    return ProductSummary(**rows[0])


@api_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "products", filter={"id": str(product_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    await delete(db, "products", {"id": str(product_id)})


@api_router.patch("/{product_id}/toggle", response_model=ProductSummary)
async def toggle_product(product_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "products", filter={"id": str(product_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    new_status = not rows[0]["is_active"]
    await update(db, "products", {"is_active": new_status, "updated_at": datetime.now(timezone.utc)}, {"id": str(product_id)})
    rows = await select(db, "products", filter={"id": str(product_id)})
    return ProductSummary(**rows[0])


# ── Variants ──────────────────────────────────────────────────────────────────

@api_router.get("/{product_id}/variants", response_model=list[VariantSummary])
async def list_variants(product_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "products", filter={"id": str(product_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return await select(db, "product_variants", filter={"product_id": str(product_id)}) or []


@api_router.post("/{product_id}/variants", response_model=VariantSummary, status_code=status.HTTP_201_CREATED)
async def add_variant(product_id: UUID, payload: VariantCreate, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "products", filter={"id": str(product_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    existing_sku = await select(db, "product_variants", filter={"sku": payload.sku})
    if existing_sku:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already used")

    data = payload.model_dump()
    data["product_id"] = str(product_id)
    data = {k: str(v) if v is not None and not isinstance(v, (bool, int, float, dict)) else v for k, v in data.items()}
    data = {k: v for k, v in data.items() if v is not None}
    await insert(db, "product_variants", data)

    rows = await select(db, "product_variants", filter={"sku": payload.sku})
    return VariantSummary(**rows[0])


@api_router.put("/{product_id}/variants/{variant_id}", response_model=VariantSummary)
async def update_variant(product_id: UUID, variant_id: UUID, payload: VariantUpdate, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "product_variants", filter={"id": str(variant_id), "product_id": str(product_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

    await update(db, "product_variants", payload.model_dump(exclude_none=True), {"id": str(variant_id)})
    rows = await select(db, "product_variants", filter={"id": str(variant_id)})
    return VariantSummary(**rows[0])


@api_router.patch("/{product_id}/variants/{variant_id}/toggle", response_model=VariantSummary)
async def toggle_variant(product_id: UUID, variant_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "product_variants", filter={"id": str(variant_id), "product_id": str(product_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

    new_status = not rows[0]["is_active"]
    await update(db, "product_variants", {"is_active": new_status, "updated_at": datetime.now(timezone.utc)}, {"id": str(variant_id)})
    rows = await select(db, "product_variants", filter={"id": str(variant_id)})
    return VariantSummary(**rows[0])


@api_router.delete("/{product_id}/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(product_id: UUID, variant_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "product_variants", filter={"id": str(variant_id), "product_id": str(product_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
    await delete(db, "product_variants", {"id": str(variant_id)})
