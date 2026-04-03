from decouple import config
from app.schemas.config import Config
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


settings = Config(
    env=config("ENV", default="development"),
    app_name=config("APP_NAME", default="Python Togo API V2.1.0"),
    debug=config("DEBUG", default=False, cast=bool),
    db_url=config("DB_URL", default="sqlite:///./test.db"),
    db_name=config("DB_NAME", default="test.db"),
    db_user=config("DB_USER", default="user"),
    db_password=config("DB_PASSWORD", default="password"),
    db_host=config("DB_HOST", default="localhost"),
    db_port=config("DB_PORT", default=5432, cast=int),
    redis_url=config("REDIS_URL", default="redis://localhost:6379/2"),
    secret_key=config("SECRET_KEY", default="your_secret_key"),
    algorithm=config("ALGORITHM", default="HS256"),
    access_token_expire_minutes=config(
        "ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int),
    log_level=config("LOG_LEVEL", default="info"),
    smtp_server=config("SMTP_SERVER", default="smtp.example.com"),
    smtp_port=config("SMTP_PORT", default=587, cast=int),
    smtp_user=config("SMTP_USER", default="user"),
    smtp_password=config("SMTP_PASSWORD", default="password")
)
