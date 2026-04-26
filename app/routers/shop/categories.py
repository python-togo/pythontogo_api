from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from datetime import datetime, timezone

from app.database.connection import get_db_connection
from app.database.orm import select, insert, update, delete
from app.schemas.shop import CategoryCreate, CategoryUpdate, CategorySummary
from app.core.security import require_admin
from app.utils.responses import success

api_router = APIRouter(prefix="/categories", tags=["shop-categories"])


@api_router.get("")
async def list_categories(db=Depends(get_db_connection), _=Depends(require_admin)):
    return success(await select(db, "categories") or [])


@api_router.post("", status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, db=Depends(get_db_connection), _=Depends(require_admin)):
    if await select(db, "categories", filter={"slug": payload.slug}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already used")
    data = payload.model_dump()
    data = {k: str(v) if hasattr(v, '__str__') and not isinstance(v, (bool, int, float, type(None))) else v for k, v in data.items()}
    await insert(db, "categories", {k: v for k, v in data.items() if v is not None})
    rows = await select(db, "categories", filter={"slug": payload.slug})
    return success(CategorySummary(**rows[0]), code=201)


@api_router.get("/{category_id}")
async def get_category(category_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "categories", filter={"id": str(category_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return success(CategorySummary(**rows[0]))


@api_router.put("/{category_id}")
async def update_category(category_id: UUID, payload: CategoryUpdate, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "categories", filter={"id": str(category_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    await update(db, "categories", payload.model_dump(exclude_none=True), {"id": str(category_id)})
    rows = await select(db, "categories", filter={"id": str(category_id)})
    return success(CategorySummary(**rows[0]))


@api_router.patch("/{category_id}/toggle")
async def toggle_category(category_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "categories", filter={"id": str(category_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    await update(db, "categories", {"is_active": not rows[0]["is_active"], "updated_at": datetime.now(timezone.utc)}, {"id": str(category_id)})
    rows = await select(db, "categories", filter={"id": str(category_id)})
    return success(CategorySummary(**rows[0]))


@api_router.delete("/{category_id}")
async def delete_category(category_id: UUID, db=Depends(get_db_connection), _=Depends(require_admin)):
    rows = await select(db, "categories", filter={"id": str(category_id)})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    await delete(db, "categories", {"id": str(category_id)})
    return success({"message": "Category deleted"})
