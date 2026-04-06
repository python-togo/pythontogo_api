from fastapi.responses import FileResponse, HTMLResponse
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
import redis.asyncio as redis
from app.core.settings import settings
from app.routers.api import api_routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_pool = AsyncConnectionPool(conninfo=settings.db_url)
    await db_pool.open()
    app.state.db_pool = db_pool

    redis_client = redis.from_url(settings.redis_url)
    app.state.redis_client = redis_client
    yield
    await app.state.db_pool.close()
    await app.state.redis_client.close()


app = FastAPI(
    title=settings.app_name,
    version="2.1.0",
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
    },
    lifespan=lifespan)


@app.get("/")
async def welcome(request: Request):
    docs_url = f"{request.base_url}docs"
    message = {
        "message": "Welcome to Python Togo official api",
        "version": "2.1.0",
        "author": "Python Software Community Togo",
        "documentations": docs_url
    }
    return message


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("app/static/favicon.ico")

app.include_router(api_routers)
