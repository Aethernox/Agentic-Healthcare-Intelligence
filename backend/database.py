"""
Database engine, session factory, and Base class.
Uses SQLite for local dev; swap DATABASE_URL for PostgreSQL in production.
"""
import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import settings

logger = logging.getLogger(__name__)

_db_url = settings.database_url
if _db_url.startswith("postgresql") and "localhost" in _db_url:
    _sqlite_path = Path(__file__).parent.parent / "data" / "medmap.db"
    _sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    _db_url = f"sqlite:///{_sqlite_path}"
    logger.info(f"Using SQLite at {_sqlite_path}")

connect_args = {"check_same_thread": False} if _db_url.startswith("sqlite") else {}
engine = create_engine(_db_url, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from models import Hospital  # noqa: F401 — registers Hospital with Base metadata
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")
