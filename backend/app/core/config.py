from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="APP_", case_sensitive=False
    )

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

    # RAG
    rag_use_real_services: bool = False
    rag_embedding_model: str = "all-MiniLM-L6-v2"
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
