"""Engine and session factory (use when wiring ride services to the DB)."""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env")


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        msg = "DATABASE_URL is not set"
        raise RuntimeError(msg)
    return url


def _connect_args() -> dict[str, Any]:
    """psycopg connect kwargs — timeout avoids hanging forever on blocked networks."""
    args: dict[str, Any] = {
        "connect_timeout": int(os.environ.get("DB_CONNECT_TIMEOUT", "10")),
    }
    sslmode = os.environ.get("DB_SSLMODE")
    if sslmode:
        args["sslmode"] = sslmode
    return args


def create_db_engine(url: Optional[str] = None, **kwargs) -> Engine:
    extra = dict(kwargs)
    if "connect_args" not in extra:
        extra["connect_args"] = _connect_args()
    return create_engine(url or get_database_url(), pool_pre_ping=True, **extra)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker[Session]] = None


def get_engine() -> Engine:
    """Process-wide engine (lazy singleton for app and tools)."""
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = create_session_factory(get_engine())
    return _session_factory


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Commit on success, rollback on error, always close."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
