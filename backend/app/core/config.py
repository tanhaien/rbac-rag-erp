from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", case_sensitive=False)

    # App
    env: str = "dev"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    secret_key: str = "change-me"

    # Datastores
    database_url: str | None = None
    redis_url: str | None = None

    # Cerbos
    cerbos_host: str | None = None
    cerbos_use_stub: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
