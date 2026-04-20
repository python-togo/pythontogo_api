from datetime import datetime, timezone

from fastapi import HTTPException

from app.database.orm import delete, insert, select, update


async def _get_event_id(db, event_code: str) -> str:
    rows = await select(db, "events", filter={"code": event_code.upper()})
    if not rows:
        raise HTTPException(status_code=404, detail=f"Event '{event_code}' not found")
    return str(rows[0]["id"])


async def _get_or_404(db, speaker_id: str) -> dict:
    rows = await select(db, "speakers", filter={"id": speaker_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Speaker not found")
    return rows[0]


async def add_speaker(db, event_code: str, payload: dict) -> dict:
    event_id = await _get_event_id(db, event_code)

    existing = await select(db, "speakers", filter={"event_id": event_id, "email": payload["email"]})
    if existing:
        raise HTTPException(status_code=409, detail="A speaker with this email already exists for this event")

    data = {k: str(v) if v is not None and not isinstance(v, (bool, int, dict)) else v
            for k, v in payload.items()}
    data = {k: v for k, v in data.items() if v is not None}
    data["event_id"] = event_id
    await insert(db, "speakers", data)

    rows = await select(db, "speakers", filter={"event_id": event_id, "email": payload["email"]})
    return rows[0]


async def get_speakers_by_event(db, event_code: str) -> list:
    event_id = await _get_event_id(db, event_code)
    return await select(db, "speakers", filter={"event_id": event_id}) or []


async def get_all_speakers(db) -> list:
    return await select(db, "speakers") or []


async def get_speaker_by_id(db, speaker_id: str) -> dict:
    return await _get_or_404(db, speaker_id)


async def update_speaker(db, speaker_id: str, payload: dict) -> dict:
    await _get_or_404(db, speaker_id)
    payload["updated_at"] = datetime.now(timezone.utc)
    data = {k: str(v) if v is not None and not isinstance(v, (bool, int, dict)) else v
            for k, v in payload.items()}
    data = {k: v for k, v in data.items() if v is not None}
    await update(db, "speakers", data, filter={"id": speaker_id})
    return await _get_or_404(db, speaker_id)


async def update_speaker_photo(db, speaker_id: str, photo_url: str) -> dict:
    await _get_or_404(db, speaker_id)
    await update(db, "speakers",
                 {"photo_url": photo_url, "updated_at": datetime.now(timezone.utc)},
                 filter={"id": speaker_id})
    return await _get_or_404(db, speaker_id)


async def delete_speaker(db, speaker_id: str) -> None:
    await _get_or_404(db, speaker_id)
    await delete(db, "speakers", filter={"id": speaker_id})
