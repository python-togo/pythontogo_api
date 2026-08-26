from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
import redis.asyncio as redis
from app.core.settings import settings
from app.routers.api import api_routers
from app.routers.auth import api_router as auth_router
from app.routers.notifications import api_router as notifications_router
from app.webhooks.payments_callback import api_router as payments_callback_router
from app.routers.feedback_public import api_router as feedback_public_router
from app.core.settings import logger, settings
from pathlib import Path
from datetime import datetime, timezone


BASE_DIR = Path(__file__).resolve().parent

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
        "http://localhost:8080/"

    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    current_time = datetime.now(timezone.utc)
    app.state.current_time = current_time
    async with AsyncConnectionPool(
            conninfo=settings.db_url,
            min_size=1, max_size=5, timeout=10,
            kwargs={"prepare_threshold": None}) as db_pool:
        app.state.db_pool = db_pool

        redis_client = redis.from_url(settings.redis_url)
        app.state.redis_client = redis_client

        yield

        await app.state.redis_client.close()


_is_dev = settings.env in ["dev", "local", "development"]

app = FastAPI(
    title=settings.app_name,
    version="2.1.0",
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
    },
    lifespan=lifespan,
    openapi_url="/openapi.json",  # if _is_dev else None,
    docs_url="/docs",            # if _is_dev else None,
    redoc_url="/redoc",          # if _is_dev else None,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def welcome():
    base_url = settings.base_url.rstrip("/")
    docs_url = f"{base_url}/docs"
    message = {
        "message": "Welcome to Python Togo official api",
        "version": "2.1.0",
        "author": "Python Software Community Togo",
        "documentations": docs_url
    }
    logger.info(f"SMTP_SERVER={settings.smtp_server}")
    logger.info(f"SMTP_PORT={settings.smtp_port}")
    return message


@app.get("/unsubscribe", status_code=200)
async def unsubscribe():
    html_content = """
    <html>
        <head>
            <title>Unsubscribe from Python Togo Emails</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .container {
                    background-color: #ffffff;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    text-align: center;
                }
                .button {
                    display: inline-block;
                    padding: 10px 20px;
                    margin-top: 20px;
                    font-size: 16px;
                    color: #ffffff;
                    background-color: #9bc6a6;
                    border: none;
                    border-radius: 5px;
                    text-decoration: none;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>You have been unsubscribed</h1>
                <p>You will no longer receive emails from Python Togo.</p>
                <a href="https://www.pytogo.org" class="button">Visit Our Website</a>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(BASE_DIR / "static" / "favicon.ico")


app.include_router(auth_router, prefix="/api/v2")
app.include_router(api_routers)
app.include_router(payments_callback_router)
app.include_router(notifications_router)
app.include_router(feedback_public_router)
