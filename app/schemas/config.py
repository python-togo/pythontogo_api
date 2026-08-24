from pydantic import BaseModel


class Config(BaseModel):
    """Config schema for the application."""

    env: str = "development"
    app_name: str = "Python Togo API V2.1.0"
    business_name: str = "Python Software Community of Togo"
    debug: bool = False
    base_url: str = "http://localhost:8008"
    root_path: str = "/api/v2"
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
    admin_api_key: str = ""
    admin_smtp_server: str | None = None
    admin_smtp_port: int | None = None
    admin_smtp_user: str | None = None
    admin_smtp_password: str | None = None
    paydunya_public_key: str | None = None
    paydunya_private_key: str | None = None
    paydunya_token: str | None = None
    paydunya_master_key: str | None = None
    webhook_secret_key: str | None = None
    webhook_url: str | None = None
    success_page_url: str | None = None
    cancel_page_url: str | None = None
    imagekit_public_key: str | None = None
    imagekit_private_key: str | None = None
    imagekit_url_endpoint: str | None = None
    student_pass_template_url: str | None = None
    professional_pass_template_url: str | None = None
    premium_pass_template_url: str | None = None
    dinner_pass_template_url: str | None = None
    volunteering_team_email: str | None = None
    ticketing_team_email: str | None = None
    sponsorship_team_email: str | None = None
    contact_team_email: str | None = None
    whatsapp_token: str | None = None
    whatsapp_api_url: str | None = None
