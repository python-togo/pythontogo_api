from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
import redis.asyncio as redis
from app.core.settings import logger, settings
from app.routers.api import api_routers
from app.routers.auth import api_router as auth_router
from app.routers.shop.api import shop_router, client_shop_router
from app.routers.admin.api import admin_router
from app.routers.registrations import api_router as registrations_router
from app.database.seed import run_seed
from app.utils.responses import error as error_response, success

origins = []
if settings.env == "development":
    origins = ["*"]
else:
    origins = [
        "https://pycontg.pytogo.org",
        "https://www.pycontg.pytogo.org",
        "https://pycon.pytogo.org",
        "https://www.pycon.pytogo.org",
        "https://pytogo.org",
        "https://www.pytogo.org",
        "https://pytogo.org",
        "https://tg.pycon.org",
        "https://api.pytogo.org",
        "https://api.pycontg.pytogo.org"
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncConnectionPool(
        conninfo=settings.db_url,
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
        timeout=settings.db_pool_timeout,
        kwargs={
            "prepare_threshold": None,
            "sslmode": settings.db_ssl_mode,
        },
    ) as db_pool:
        app.state.db_pool = db_pool
        logger.info(
            "Database pool ready (min=%d max=%d ssl=%s)",
            settings.db_pool_min_size,
            settings.db_pool_max_size,
            settings.db_ssl_mode,
        )

        redis_client = redis.from_url(settings.redis_url)
        app.state.redis_client = redis_client

        await run_seed(db_pool)

        yield

        await app.state.redis_client.close()


app = FastAPI(
    title=settings.app_name,
    version="2.1.0",
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
    },
    lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global exception handlers — ensure every error follows the standard envelope
# ---------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return error_response(message=str(exc.detail), code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error_response(message="Validation error", code=422, details=exc.errors())


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return error_response(message="Internal server error", code=500)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def welcome(request: Request):
    docs_url = f"{request.base_url}docs"
    return {
        "message": "Welcome to Python Togo official api",
        "version": "2.1.0",
        "author": "Python Software Community Togo",
        "documentations": docs_url
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("app/static/favicon.ico")


@app.get("/api/v2/health", tags=["health"])
async def health_check(request: Request):
    """Vérification de la connectivité base de données et Redis."""
    report: dict = {
        "status": "healthy",
        "version": "2.1.0",
        "database": {"status": "unknown", "detail": None},
        "redis": {"status": "unknown", "detail": None},
    }

    # ── Database ──────────────────────────────────────────────────────────────
    try:
        async with request.app.state.db_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT version()")
                row = await cur.fetchone()
        report["database"] = {"status": "connected", "detail": row[0] if row else None}
    except Exception as exc:
        report["database"] = {"status": "error", "detail": str(exc)}
        report["status"] = "degraded"
        logger.error("Health check — DB error: %s", exc)

    # ── Redis ─────────────────────────────────────────────────────────────────
    try:
        pong = await request.app.state.redis_client.ping()
        report["redis"] = {"status": "connected" if pong else "no-response", "detail": None}
        if not pong:
            report["status"] = "degraded"
    except Exception as exc:
        report["redis"] = {"status": "error", "detail": str(exc)}
        report["status"] = "degraded"
        logger.error("Health check — Redis error: %s", exc)

    http_code = 200 if report["status"] == "healthy" else 503
    return success(report, code=http_code)


app.include_router(auth_router, prefix="/api/v2")
app.include_router(shop_router, prefix="/api/v2")
app.include_router(client_shop_router, prefix="/api/v2")
app.include_router(admin_router, prefix="/api/v2")
app.include_router(registrations_router, prefix="/api/v2")
app.include_router(api_routers)
