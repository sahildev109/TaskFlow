import re

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.core.logging import app_logger


# ── Engine ────────────────────────────────────────────────────────────────────

engine = create_async_engine(
    re.sub(r"^postgresql:", "postgresql+asyncpg:", settings.DATABASE_URL),
    poolclass=NullPool,  # Neon PG works best with NullPool (serverless)
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ── Base Model ────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Dependency ────────────────────────────────────────────────────────────────

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Startup / Shutdown ────────────────────────────────────────────────────────

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app_logger.info("Database tables initialized")


async def close_db():
    await engine.dispose()
    app_logger.info("Database connection closed")
