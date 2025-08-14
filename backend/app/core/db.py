from __future__ import annotations

from collections.abc import Generator, Iterator
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..auth.models import Base
from .config import get_settings

_engine = None
_SessionLocal: Optional[sessionmaker] = None


def init_engine() -> None:
    global _engine, _SessionLocal
    settings = get_settings()
    if settings.database_url:
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    else:
        _engine = None
        _SessionLocal = None


@contextmanager
def get_session() -> Iterator[Session]:
    if _SessionLocal is None:
        init_engine()
    if _SessionLocal is None:
        # Database not configured; raise informative error when actually used
        raise RuntimeError(
            "Database URL not configured. Set APP_DATABASE_URL to enable DB access."
        )
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all_if_configured() -> None:
    """Create tables if a database is configured.
    Safe no-op when no DB URL is set.
    """
    if _SessionLocal is None:
        init_engine()
    if _engine is not None:
        Base.metadata.create_all(bind=_engine)


def db_available() -> bool:
    """Return True if a database engine/session is configured."""
    if _SessionLocal is None:
        init_engine()
    return _SessionLocal is not None


def db_dependency() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a Session or raises if DB is not configured."""
    if not db_available():
        raise RuntimeError("Database not available. Set APP_DATABASE_URL.")
    with get_session() as s:
        yield s
