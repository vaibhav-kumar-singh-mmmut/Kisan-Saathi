"""SQLAlchemy engine + session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.core.config import settings

# Strip async driver prefix if present for synchronous operations
_sync_url = settings.DB_URL.replace("+asyncpg", "").replace("+aiosqlite", "")

_connect_args = {"check_same_thread": False} if "sqlite" in _sync_url else {}

engine = create_engine(
    _sync_url,
    echo=(settings.APP_ENV == "development"),
    pool_pre_ping=True,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    pass


def get_db():
    """FastAPI dependency — yields a DB session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
