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
    smtp_from_email: str = "no-reply@example.com"
    smtp_from_name: str = "Python Togo"
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    cloudinary_folder: str = "pythontogo"
    db_pool_min_size: int = 1
    db_pool_max_size: int = 5
    db_pool_timeout: int = 10
    db_ssl_mode: str = "require"
    superadmin_email: str = "superadmin@pytogo.org"
    superadmin_username: str = "superadmin"
    superadmin_password: str = "ChangeMe!2025"
    superadmin_full_name: str = "Super Admin"
