"""Standardised API response helpers.

Every endpoint returns one of these two shapes:

Success:
    {
        "success": true,
        "code": 200,
        "data": <any>,
        "meta": { "timestamp": "...", "version": "2.1.0", "total"?: N, "page"?: N, "per_page"?: N }
    }

Error (also used by the global exception handlers in main.py):
    {
        "success": false,
        "code": 4xx|5xx,
        "data": null,
        "error": { "message": "...", "details": <any> },
        "meta": { "timestamp": "...", "version": "2.1.0" }
    }
"""

from datetime import datetime, timezone
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

APP_VERSION = "2.1.0"


def _meta(total: int | None = None, page: int | None = None, per_page: int | None = None) -> dict:
    m: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": APP_VERSION,
    }
    if total is not None:
        m["total"] = total
    if page is not None:
        m["page"] = page
    if per_page is not None:
        m["per_page"] = per_page
    return m


def success(
    data: Any = None,
    code: int = 200,
    total: int | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=code,
        content={
            "success": True,
            "code": code,
            "data": jsonable_encoder(data),
            "meta": _meta(total=total, page=page, per_page=per_page),
        },
    )


def error(
    message: str,
    code: int = 400,
    details: Any = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=code,
        content={
            "success": False,
            "code": code,
            "data": None,
            "error": {"message": message, "details": jsonable_encoder(details)},
            "meta": _meta(),
        },
    )
