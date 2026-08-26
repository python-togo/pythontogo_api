from decouple import config
from app.schemas.config import Config
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


settings = Config(
    env=config("ENV", default="development"),
    app_name=config("APP_NAME", default="Python Togo API V2.1.0"),
    debug=config("DEBUG", default=False, cast=bool),
    business_name=config(
        "BUSINESS_NAME", default="Python Software Community of Togo"),
    base_url=config("BASE_URL", default="http://localhost:8008"),
    root_path=config("ROOT_PATH", default="/api/v2"),
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
    smtp_password=config("SMTP_PASSWORD", default="password"),
    admin_api_key=config("ADMIN_API_KEY", default=""),
    admin_smtp_server=config("ADMIN_SMTP_SERVER", default=None),
    admin_smtp_port=config("ADMIN_SMTP_PORT", default=None),
    admin_smtp_user=config("ADMIN_SMTP_USER", default=None),
    admin_smtp_password=config("ADMIN_SMTP_PASSWORD", default=None),
    paydunya_public_key=config("PAYDUNYA_PUBLIC_KEY", default=None),
    paydunya_private_key=config("PAYDUNYA_PRIVATE_KEY", default=None),
    paydunya_token=config("PAYDUNYA_TOKEN", default=None),
    paydunya_master_key=config("PAYDUNYA_MASTER_KEY", default=None),
    webhook_secret_key=config("WEBHOOK_SECRET_KEY", default=None),
    webhook_url=config("WEBHOOK_URL", default=None),
    success_page_url=config("SUCCESS_PAGE_URL", default=None),
    cancel_page_url=config("CANCEL_PAGE_URL", default=None),
    imagekit_private_key=config("IMAGEKIT_PRIVATE_KEY", default=None),
    imagekit_public_key=config("IMAGEKIT_PUBLIC_KEY", default=None),
    imagekit_url_endpoint=config("IMAGEKIT_URL_ENDPOINT", default=None),
    student_pass_template_url=config(
        "STUDENT_PASS_TEMPLATE_URL", default=None),
    professional_pass_template_url=config(
        "PROFESSIONAL_PASS_TEMPLATE_URL", default=None),
    premium_pass_template_url=config(
        "PREMIUM_PASS_TEMPLATE_URL", default=None),
    dinner_pass_template_url=config("DINNER_PASS_TEMPLATE_URL", default=None),
    volunteering_team_email=config("VOLUNTEERING_TEAM_EMAIL", default=None),
    ticketing_team_email=config("TICKETING_TEAM_EMAIL", default=None),
    sponsorship_team_email=config("SPONSORSHIP_TEAM_EMAIL", default=None),
    contact_team_email=config("CONTACT_TEAM_EMAIL", default=None),
    whatsapp_token=config("WHATSAPP_TOKEN", default=None),
    whatsapp_api_url=config("WHATSAPP_API_URL", default=None)
)


infos = {
    'name': settings.business_name,
    'tagline': "Python Software Community of Togo - Promoting Python in Togo",
    'postal_address': "Lome, Togo",
    'phone_number': "+22898273805",
    'website_url': "https://pycon.pytogo.org/",
    'logo_url': "https://ik.imagekit.io/pythontogo/images/pythontogo/pythontogo.png?updatedAt=1777729231402"
}
