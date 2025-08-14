from __future__ import annotations
from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .config import get_settings
from ..auth.models import Base

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
        raise RuntimeError("Database URL not configured. Set APP_DATABASE_URL to enable DB access.")
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
