from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from redis.asyncio import Redis
from app.core.settings import settings
from app.routers.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_pool = AsyncConnectionPool(conninfo=settings.db_url)
    app.state.db_pool = db_pool
    await db_pool.open()

    yield
    await app.state.db_pool.close()


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
    docs_url = f"{request.base_url}{app.docs_url[1:]}"
    print(docs_url)
    message = {
        "message": "Welcome to Python Togo official api",
        "version": "2.1.0",
        "author": "Python Software Community Togo",
        "documentations": docs_url
    }
    return message


app.include_router(api_router)
