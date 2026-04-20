from datetime import datetime, timezone

from fastapi import HTTPException
from psycopg.rows import dict_row

from app.database.orm import delete, insert, select, update


async def _get_event_id(db, event_code: str) -> str:
    rows = await select(db, "events", filter={"code": event_code.upper()})
    if not rows:
        raise HTTPException(status_code=404, detail=f"Event '{event_code}' not found")
    return str(rows[0]["id"])


async def _get_or_404(db, session_id: str) -> dict:
    rows = await select(db, "sessions", filter={"id": session_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Session not found")
    return rows[0]


async def add_session(db, event_code: str, payload: dict) -> dict:
    event_id = await _get_event_id(db, event_code)

    existing = await select(db, "sessions", filter={"slug": payload["slug"]})
    if existing:
        raise HTTPException(status_code=409, detail=f"Slug '{payload['slug']}' is already used")

    data = {k: str(v) if v is not None and not isinstance(v, (bool, int, datetime)) else v
            for k, v in payload.items()}
    data = {k: v for k, v in data.items() if v is not None}
    data["event_id"] = event_id
    await insert(db, "sessions", data)

    rows = await select(db, "sessions", filter={"slug": payload["slug"]})
    return rows[0]


async def get_sessions_by_event(db, event_code: str) -> list:
    event_id = await _get_event_id(db, event_code)
    return await select(db, "sessions", filter={"event_id": event_id}) or []


async def get_all_sessions(db) -> list:
    return await select(db, "sessions") or []


async def get_session_by_id(db, session_id: str) -> dict:
    return await _get_or_404(db, session_id)


async def update_session(db, session_id: str, payload: dict) -> dict:
    await _get_or_404(db, session_id)

    if "slug" in payload:
        existing = await select(db, "sessions", filter={"slug": payload["slug"]})
        if existing and str(existing[0]["id"]) != session_id:
            raise HTTPException(status_code=409, detail=f"Slug '{payload['slug']}' is already used")

    data = {k: str(v) if v is not None and not isinstance(v, (bool, int, datetime)) else v
            for k, v in payload.items()}
    data = {k: v for k, v in data.items() if v is not None}
    data["updated_at"] = datetime.now(timezone.utc)
    await update(db, "sessions", data, filter={"id": session_id})
    return await _get_or_404(db, session_id)


async def delete_session(db, session_id: str) -> None:
    await _get_or_404(db, session_id)
    await delete(db, "sessions", filter={"id": session_id})


async def get_sessions_schedule(db, event_code: str) -> list[dict]:
    """Sessions d'un event triées par starts_at avec speakers et tracks."""
    event_id = await _get_event_id(db, event_code)
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                s.id, s.title, s.slug, s.session_type,
                s.starts_at, s.ends_at, s.description,
                s.venue_id, s.track_id, s.proposal_id,
                t.name  AS track_name,  t.color AS track_color,
                sp.full_name AS speaker_name, sp.headline AS speaker_headline,
                sp.photo_url AS speaker_photo_url
            FROM sessions s
            LEFT JOIN tracks t   ON t.id  = s.track_id
            LEFT JOIN speakers sp ON sp.id = s.speaker_id
            WHERE s.event_id = %s
            ORDER BY s.starts_at ASC
            """,
            (event_id,),
        )
        return await cur.fetchall()
