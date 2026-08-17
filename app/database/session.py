"""
Legal AI System - Database Session Management
===============================================
Async database session factory and dependency for FastAPI.
Engine and session are created lazily to avoid import-time connection issues.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass


# --- Lazy initialization ---
# Engine and session factory are created on first use, not on import.
_engine = None
_async_session_factory = None


def _get_engine():
    """Create engine lazily on first call."""
    global _engine
    if _engine is None:
        from app.config import get_settings
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.is_development,
            pool_size=5,
            max_overflow=5,
            pool_pre_ping=True,
            pool_timeout=30,
            pool_recycle=1800,
        )
    return _engine


def _get_session_factory():
    """Create session factory lazily on first call."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that provides an async database session.
    Automatically commits on success and rolls back on error.

    Usage in routers:
        @router.get("/")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
