from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from swaram.config.settings import get_settings
from swaram.core.logging import get_logger
from swaram.models.base import Base

logger = get_logger("storage.postgres")

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        engine = get_engine()
        _sessionmaker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _sessionmaker


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager providing an isolated database session."""
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db(engine: AsyncEngine | None = None) -> None:
    """Initialize database tables and create TimescaleDB hypertables if supported."""
    eng = engine or get_engine()
    logger.info("Initializing database schema...")
    
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Check if TimescaleDB is available and create hypertables
        try:
            res = await conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'timescaledb';"))
            if res.scalar():
                logger.info("TimescaleDB extension detected, converting tables to hypertables...")
                hypertables = [
                    ("ticks", "timestamp"),
                    ("trades", "timestamp"),
                    ("candles", "timestamp"),
                    ("orderbook_snapshots", "timestamp"),
                    ("funding", "timestamp"),
                    ("open_interest", "timestamp"),
                ]
                for tbl, time_col in hypertables:
                    try:
                        await conn.execute(text(
                            f"SELECT create_hypertable('{tbl}', '{time_col}', if_not_exists => TRUE, migrate_data => TRUE);"
                        ))
                    except Exception as e:
                        logger.warning(f"Could not convert {tbl} to hypertable: {e}")
        except Exception as e:
            logger.info("TimescaleDB check skipped or not active on standard postgres instance", error=str(e))
            
    logger.info("Database schema initialized successfully.")


async def close_db() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None
        logger.info("Postgres connection pool closed.")
