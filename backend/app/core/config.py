from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str = "development"
    APP_NAME: str = "Team Task Board"
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "postgresql+asyncpg://ttb:ttb_password@db:5432/ttb_db"
    REDIS_URL: str = "redis://redis:6379/0"
    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
