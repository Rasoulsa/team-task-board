from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str = "development"
    APP_NAME: str = "Team Task Board"
    SECRET_KEY: str = "team-task-board-dev-secret-key-minimum-32-characters-long"

    # JWT / Authentication
    JWT_SECRET_KEY: str = "team-task-board-dev-secret-key-minimum-32-characters-long"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # Authentication rate limiting
    AUTH_RATE_LIMIT_TIMES: int = 10
    AUTH_RATE_LIMIT_SECONDS: int = 60

    # Local development defaults.
    # When backend runs inside Docker, docker-compose should override these.
    DATABASE_URL: str = "postgresql+asyncpg://ttb:ttb_password@localhost:55432/ttb_db"
    REDIS_URL: str = "redis://localhost:6380/0"

    # Frontend / CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"
    # FRONTEND_URL: str = "http://localhost:5173"

    # Celery / broker
    CELERY_BROKER_URL: str = "redis://localhost:6379/2"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/3"

    # Email (SMTP) — for local dev, MailHog on 1025 works with no auth
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "no-reply@teamtaskboard.local"
    SMTP_USE_TLS: bool = False

    # Due-date reminder window (hours before due date to remind)
    DUE_REMINDER_HOURS: int = 24

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
