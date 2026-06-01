from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.logging import app_logger
from app.db.session import init_db, close_db
from app.db.redis import close_redis
from app.api.v1 import api_router
from app.middleware.exceptions import (
    validation_exception_handler,
    integrity_error_handler,
    generic_exception_handler,
)
from app.middleware.logging import RequestLoggingMiddleware

import os
os.makedirs("logs", exist_ok=True)


# ── Rate Limiter ──────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    yield
    await close_db()
    await close_redis()
    app_logger.info("Shutdown complete")


# ── App Factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## TaskFlow API — Scalable REST API with Auth & RBAC

### Features
- **JWT Authentication** with access + refresh token rotation
- **Role-Based Access Control** (USER / ADMIN)
- **Task Management** CRUD with soft delete, filtering, pagination
- **Redis Caching** for read performance + token blacklisting on logout
- **Rate Limiting** via SlowAPI (60 req/min default)
- **Request Logging** with latency headers
- **Async SQLAlchemy** on Neon PostgreSQL

### Auth Flow
1. `POST /api/v1/auth/register` — create account
2. `POST /api/v1/auth/login` — get access + refresh tokens
3. Use `Authorization: Bearer <access_token>` header on protected routes
4. `POST /api/v1/auth/refresh` — rotate access token
5. `POST /api/v1/auth/logout` — blacklist token

### Roles
| Role | Permissions |
|------|-------------|
| USER | Own profile, own tasks CRUD |
| ADMIN | All users, all tasks |
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── Middleware (order matters — outermost = last to run on response) ───────────

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception Handlers ────────────────────────────────────────────────────────

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ── Routes ────────────────────────────────────────────────────────────────────

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"], include_in_schema=False)
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
