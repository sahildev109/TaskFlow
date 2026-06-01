from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.db.redis import get_redis
from app.schemas.common import HealthResponse
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Checks database and Redis connectivity.",
)
async def health_check(db: AsyncSession = Depends(get_db)):
    # Check DB
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"

    # Check Redis
    redis_status = "ok"
    try:
        r = await get_redis()
        await r.ping()
    except Exception as e:
        redis_status = f"error: {str(e)[:50]}"

    return HealthResponse(
        status="healthy" if db_status == "ok" and redis_status == "ok" else "degraded",
        version=settings.APP_VERSION,
        database=db_status,
        redis=redis_status,
        environment=settings.ENVIRONMENT,
    )
