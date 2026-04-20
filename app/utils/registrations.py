from datetime import datetime, timezone

from fastapi import HTTPException
from psycopg.rows import dict_row

from app.database.orm import delete, insert, select, update


async def get_event_id_by_code(db, event_code: str) -> str:
    rows = await select(db, "events", filter={"code": event_code.upper()})
    if not rows:
        raise HTTPException(status_code=404, detail=f"Event '{event_code}' not found")
    return str(rows[0]["id"])


async def register_participant(db, event_code: str, payload: dict, user_id: str | None = None):
    event_id = await get_event_id_by_code(db, event_code)

    existing = await select(db, "registrations", filter={"event_id": event_id, "email": payload["email"]})
    if existing:
        raise HTTPException(status_code=409, detail="This email is already registered for this event")

    data = {**payload, "event_id": event_id}
    if user_id:
        data["user_id"] = user_id
    await insert(db, "registrations", data)

    rows = await select(db, "registrations", filter={"event_id": event_id, "email": payload["email"]})
    return rows[0]


async def get_registrations_by_event(db, event_code: str) -> list:
    event_id = await get_event_id_by_code(db, event_code)
    return await select(db, "registrations", filter={"event_id": event_id}) or []


async def get_registration_by_id(db, registration_id: str) -> dict:
    rows = await select(db, "registrations", filter={"id": registration_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Registration not found")
    return rows[0]


async def update_registration(db, registration_id: str, payload: dict):
    await get_registration_by_id(db, registration_id)
    payload["updated_at"] = datetime.now(timezone.utc)
    await update(db, "registrations", payload, filter={"id": registration_id})
    return await get_registration_by_id(db, registration_id)


async def update_registration_status(db, registration_id: str, status: str):
    await get_registration_by_id(db, registration_id)
    data: dict = {"status": status, "updated_at": datetime.now(timezone.utc)}
    if status == "checked_in":
        data["checked_in_at"] = datetime.now(timezone.utc)
    await update(db, "registrations", data, filter={"id": registration_id})
    return await get_registration_by_id(db, registration_id)


async def delete_registration(db, registration_id: str):
    await get_registration_by_id(db, registration_id)
    await delete(db, "registrations", filter={"id": registration_id})


async def get_registrations_dashboard(db, event_code: str) -> dict:
    event_id = await get_event_id_by_code(db, event_code)

    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT COUNT(*) AS total FROM registrations WHERE event_id = %s",
            (event_id,),
        )
        total = (await cur.fetchone())["total"]

        await cur.execute(
            "SELECT status, COUNT(*) AS cnt FROM registrations WHERE event_id = %s GROUP BY status",
            (event_id,),
        )
        by_status = {r["status"]: r["cnt"] for r in await cur.fetchall()}

        await cur.execute(
            "SELECT ticket_type, COUNT(*) AS cnt FROM registrations WHERE event_id = %s GROUP BY ticket_type",
            (event_id,),
        )
        by_ticket_type = {r["ticket_type"]: r["cnt"] for r in await cur.fetchall()}

        await cur.execute(
            "SELECT COUNT(*) AS total FROM registrations "
            "WHERE event_id = %s AND status = 'checked_in' "
            "AND checked_in_at >= CURRENT_DATE",
            (event_id,),
        )
        checked_in_today = (await cur.fetchone())["total"]

    return {
        "total": total,
        "by_status": by_status,
        "by_ticket_type": by_ticket_type,
        "checked_in_today": checked_in_today,
    }
