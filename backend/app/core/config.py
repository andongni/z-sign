import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Runtime settings, kept compatible with the old Django env names."""

    app_name = "AI智能合同审核系统"
    debug = os.getenv("DEBUG", "True") == "True"
    secret_key = os.getenv("SECRET_KEY", "django-insecure-change-this-in-production")
    algorithm = "HS256"
    access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    media_root = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media")))
    media_url = "/media"
    upload_max_size = int(os.getenv("FILE_UPLOAD_MAX_MEMORY_SIZE", str(10 * 1024 * 1024)))

    cors_allowed_origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:5174,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:3000,http://36.134.27.102:8848",
        ).split(",")
        if origin.strip()
    ]

    @property
    def database_url(self) -> str:
        explicit = os.getenv("DATABASE_URL")
        if explicit:
            return explicit

        name = os.getenv("DB_NAME", "contract_review")
        user = quote_plus(os.getenv("DB_USER", "root"))
        password = quote_plus(os.getenv("DB_PASSWORD", ""))
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "3306")
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


@lru_cache
def get_settings() -> Settings:
    return Settings()
