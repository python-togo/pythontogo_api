from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
import redis.asyncio as redis
from app.core.settings import settings
from app.routers.api import api_routers
from app.routers.auth import api_router as auth_router
from app.routers.shop.api import shop_router, client_shop_router

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
        # "http://127.0.0.1:8080/",
        # "http://localhost:8080/"

    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncConnectionPool(
            conninfo=settings.db_url,
            min_size=1, max_size=5, timeout=10,
            kwargs={"prepare_threshold": None}) as db_pool:
        app.state.db_pool = db_pool

        redis_client = redis.from_url(settings.redis_url)
        app.state.redis_client = redis_client

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

app.include_router(auth_router, prefix="/api/v2")
app.include_router(shop_router, prefix="/api/v2")
app.include_router(client_shop_router, prefix="/api/v2")
app.include_router(api_routers)
