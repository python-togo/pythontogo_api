from pydantic import BaseModel


class Config(BaseModel):
    """Config schema for the application."""

    env: str = "development"
    app_name: str = "Python Togo API V2.1.0"
    debug: bool = False
    db_url: str = "sqlite:///./test.db"
    db_name: str = "test.db"
    db_user: str = "user"
    db_password: str = "password"
    db_host: str = "localhost"
    db_port: int = 5432
    redis_url: str = "redis://localhost:6379/2"
    secret_key: str = "your_secret_key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    log_level: str = "info"
    smtp_server: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_user: str = "user"
    smtp_password: str = "password"
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    cloudinary_folder: str = "pythontogo"
