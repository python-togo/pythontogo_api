from datetime import datetime, timezone

from fastapi import HTTPException
from psycopg.rows import dict_row

from app.database.orm import delete, insert, select, update


async def _get_event_id(db, event_code: str) -> str:
    rows = await select(db, "events", filter={"code": event_code.upper()})
    if not rows:
        raise HTTPException(status_code=404, detail=f"Event '{event_code}' not found")
    return str(rows[0]["id"])


async def _get_or_404(db, package_id: str) -> dict:
    rows = await select(db, "sponsor_packages", filter={"id": package_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Sponsor package not found")
    return rows[0]


async def create_package(db, event_code: str, payload: dict) -> dict:
    event_id = await _get_event_id(db, event_code)

    existing = await select(db, "sponsor_packages",
                            filter={"event_id": event_id, "tier": payload["tier"]})
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A package with tier '{payload['tier']}' already exists for this event",
        )

    data = {**payload, "event_id": event_id}
    await insert(db, "sponsor_packages", data)

    rows = await select(db, "sponsor_packages",
                        filter={"event_id": event_id, "tier": payload["tier"]})
    return rows[0]


async def get_packages_by_event(db, event_code: str) -> list[dict]:
    event_id = await _get_event_id(db, event_code)
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT p.*,
                   COUNT(sp.id) FILTER (WHERE sp.is_confirmed = true) AS slots_used
            FROM sponsor_packages p
            LEFT JOIN sponsors_partners sp ON sp.package_id = p.id
            WHERE p.event_id = %s
            GROUP BY p.id
            ORDER BY p.price DESC
            """,
            (event_id,),
        )
        return await cur.fetchall()


async def get_package_by_id(db, package_id: str) -> dict:
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT p.*,
                   COUNT(sp.id) FILTER (WHERE sp.is_confirmed = true) AS slots_used
            FROM sponsor_packages p
            LEFT JOIN sponsors_partners sp ON sp.package_id = p.id
            WHERE p.id = %s
            GROUP BY p.id
            """,
            (package_id,),
        )
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sponsor package not found")
    return row


async def update_package(db, package_id: str, payload: dict) -> dict:
    await _get_or_404(db, package_id)
    payload["updated_at"] = datetime.now(timezone.utc)
    await update(db, "sponsor_packages", payload, filter={"id": package_id})
    return await get_package_by_id(db, package_id)


async def delete_package(db, package_id: str) -> None:
    pkg = await _get_or_404(db, package_id)
    sponsors = await select(db, "sponsors_partners", filter={"package_id": package_id})
    if sponsors:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a package that has sponsors assigned. Reassign or remove them first.",
        )
    await delete(db, "sponsor_packages", filter={"id": package_id})


async def assign_package_to_sponsor(db, sponsor_id: str, package_id: str | None) -> dict:
    sponsors = await select(db, "sponsors_partners", filter={"id": sponsor_id})
    if not sponsors:
        raise HTTPException(status_code=404, detail="Sponsor not found")

    data: dict = {"updated_at": datetime.now(timezone.utc)}

    if package_id:
        pkg = await get_package_by_id(db, package_id)
        if not pkg["is_active"]:
            raise HTTPException(status_code=400, detail="This package is no longer active")
        if pkg["max_slots"] and pkg["slots_used"] >= pkg["max_slots"]:
            raise HTTPException(status_code=409, detail="No slots available for this package")
        data["package_id"] = package_id
        data["package_tier"] = pkg["tier"]
    else:
        data["package_id"] = None

    await update(db, "sponsors_partners", data, filter={"id": sponsor_id})
    rows = await select(db, "sponsors_partners", filter={"id": sponsor_id})
    return rows[0]
