# ⚡ TaskFlow

A production-grade **REST API** with **JWT Authentication**, **Role-Based Access Control**, and a **Next.js frontend** dashboard.

Built with: **FastAPI · PostgreSQL (Neon) · Redis · Next.js · TypeScript · Tailwind CSS**

---

## Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Security Design](#security-design)
- [Scalability Notes](#scalability-notes)
- [Deployment](#deployment)

---
![Signup page](image-1.png)
![Dashboard](image.png)

## Architecture

```
┌─────────────────────┐        ┌──────────────────────────────────────┐
│   Next.js Frontend  │──────▶ │          FastAPI Backend             │
│  (Port 3000)        │  HTTP  │  (Port 8000)                         │
│                     │        │                                      │
│  /login             │        │  POST /api/v1/auth/register          │
│  /register          │        │  POST /api/v1/auth/login             │
│  /dashboard         │        │  GET  /api/v1/auth/me                │
└─────────────────────┘        │  POST /api/v1/auth/refresh           │
                                │  POST /api/v1/auth/logout            │
                                │                                      │
                                │  GET/POST  /api/v1/tasks/            │
                                │  GET/PATCH/DELETE /api/v1/tasks/{id} │
                                │                                      │
                                │  GET/PATCH /api/v1/users/me          │
                                │  [Admin] GET /api/v1/users/          │
                                └──────────────┬───────────────────────┘
                                               │
                              ┌────────────────┼───────────────────┐
                              │                │                   │
                     ┌────────▼──────┐  ┌──────▼──────┐   ┌───────▼──────┐
                     │  Neon Postgres │  │    Redis    │   │  Middleware  │
                     │  (Async ORM)  │  │  Blacklist  │   │  Rate Limit  │
                     │  SQLAlchemy   │  │  + Cache    │   │  + Logging   │
                     └───────────────┘  └─────────────┘   └─────────────-┘
```

---

## Features

### Backend (Primary)
- ✅ **JWT Auth** — access token (30min) + refresh token (7 days) rotation
- ✅ **Token Blacklisting** — logout invalidates tokens instantly via Redis
- ✅ **Role-Based Access Control** — `USER` and `ADMIN` roles, enforced via FastAPI dependencies
- ✅ **Task CRUD** — create, read, update, soft-delete with full validation
- ✅ **Filtering + Pagination** — filter by status/priority/search, paginated responses
- ✅ **Redis Caching** — individual task reads cached for 2 minutes, cache-busted on writes
- ✅ **Rate Limiting** — 60 requests/minute per IP via SlowAPI
- ✅ **Request Logging** — structured logs with latency, method, path, status via Loguru
- ✅ **Input Sanitization** — Pydantic v2 validators with regex, length limits, email checks
- ✅ **Async SQLAlchemy** — non-blocking DB layer on Neon PostgreSQL with asyncpg
- ✅ **Soft Delete** — tasks are flagged `is_deleted=true`, data retained for audit
- ✅ **API Versioning** — all routes prefixed `/api/v1/`, ready for v2 side-by-side
- ✅ **OpenAPI Docs** — auto-generated Swagger UI at `/docs`, ReDoc at `/redoc`
- ✅ **Postman Collection** — importable collection with auto-token scripts
- ✅ **Database Migrations** — Alembic async migrations
- ✅ **Test Suite** — pytest-asyncio with in-memory SQLite for fast CI

### Frontend
- ✅ Register & login with form validation
- ✅ Protected dashboard (redirects to `/login` if unauthenticated)
- ✅ Full CRUD on tasks — inline edit, status/priority badges, search + filters
- ✅ Axios interceptor auto-refreshes expired access tokens silently
- ✅ Success/error toast notifications on every action
- ✅ Admin badge shown in navbar for admin users

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI 0.111 |
| Language | Python 3.12 |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL via Neon (asyncpg driver) |
| Migrations | Alembic |
| Caching / Blacklist | Redis (Upstash in prod) |
| Auth | JWT via `python-jose`, bcrypt via `passlib` |
| Validation | Pydantic v2 |
| Rate Limiting | SlowAPI |
| Logging | Loguru |
| Frontend | Next.js 14 App Router + TypeScript |
| Styling | Tailwind CSS |
| HTTP Client | Axios |
| Forms | React Hook Form |
| Containerization | Docker + Docker Compose |

---

## Project Structure

```
taskflow/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py          # Router aggregator
│   │   │       ├── deps/
│   │   │       │   └── __init__.py      # get_current_user, require_admin deps
│   │   │       └── endpoints/
│   │   │           ├── auth.py          # /auth/*
│   │   │           ├── tasks.py         # /tasks/*
│   │   │           ├── users.py         # /users/* (admin)
│   │   │           └── health.py        # /health
│   │   ├── core/
│   │   │   ├── config.py               # Pydantic settings from .env
│   │   │   ├── security.py             # JWT create/decode, password hash
│   │   │   └── logging.py              # Loguru setup
│   │   ├── db/
│   │   │   ├── session.py              # Async engine, session factory, Base
│   │   │   └── redis.py                # Redis client, blacklist, cache helpers
│   │   ├── middleware/
│   │   │   ├── exceptions.py           # Global exception handlers
│   │   │   └── logging.py              # Request/response logging middleware
│   │   ├── models/
│   │   │   ├── user.py                 # User SQLAlchemy model
│   │   │   └── task.py                 # Task model (with soft delete)
│   │   ├── schemas/
│   │   │   ├── user.py                 # User request/response Pydantic schemas
│   │   │   ├── task.py                 # Task schemas + filter
│   │   │   └── common.py              # SuccessResponse, ErrorResponse, Health
│   │   ├── services/
│   │   │   ├── auth_service.py         # Register, login, refresh, logout logic
│   │   │   ├── task_service.py         # Task CRUD with caching
│   │   │   └── user_service.py         # User CRUD (admin ops)
│   │   └── main.py                     # App factory, middleware, lifespan
│   ├── alembic/
│   │   ├── env.py                      # Async Alembic config
│   │   └── versions/                   # Migration files
│   ├── tests/
│   │   └── test_api.py                 # Auth + task tests (pytest-asyncio)
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── pytest.ini
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx              # Root layout + AuthProvider + Toaster
│   │   │   ├── page.tsx                # Redirects to /dashboard
│   │   │   ├── globals.css
│   │   │   ├── login/page.tsx
│   │   │   ├── register/page.tsx
│   │   │   └── dashboard/page.tsx      # Main task management UI
│   │   ├── hooks/
│   │   │   └── useAuth.tsx             # Auth context + login/logout
│   │   └── lib/
│   │       └── api.ts                  # Axios instance + authAPI + tasksAPI
│   ├── Dockerfile
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── package.json
│
├── TaskFlow_API.postman_collection.json
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- A [Neon](https://neon.tech) PostgreSQL database (free tier works)
- Redis — local or [Upstash](https://upstash.com) (free tier works)

---

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/taskflow.git
cd taskflow
```

---

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL, SECRET_KEY, REDIS_URL
```

**`.env` minimum config:**
```env
DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/neondb?ssl=require
SECRET_KEY=your-32-char-random-secret
REDIS_URL=redis://localhost:6379
```

```bash
# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8000
```

API is live at **http://localhost:8000**  
Swagger docs: **http://localhost:8000/docs**

---

## API Documentation & Postman Collection

This repository includes a ready-to-import Postman collection for testing the backend endpoints:

- Postman collection: [TaskFlow_API.postman_collection.json](TaskFlow_API.postman_collection.json)
- Import this file directly into Postman to access the prepared requests for auth, tasks, and users.

You can also use the built-in interactive API docs while the backend is running locally:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Swagger UI is useful for quick browser-based testing, while Postman is better for saved collections and repeatable request workflows.

---

### 3. Frontend setup

```bash
cd ../frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Start dev server
npm run dev
```

Frontend is live at **http://localhost:3000**

---

### 4. Docker Compose (full stack)

```bash
# From project root
cp backend/.env.example backend/.env
# Edit backend/.env with your DATABASE_URL and SECRET_KEY

docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger: http://localhost:8000/docs

---

### 5. Create an admin user

After registering via `/api/v1/auth/register`, promote a user to admin directly in Postgres:

```sql
UPDATE users SET role = 'admin' WHERE email = 'your@email.com';
```

---

### 6. Run tests

```bash
cd backend
pip install aiosqlite  # SQLite async driver for test isolation
pytest -v
```

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | ✗ | Register new user |
| POST | `/auth/login` | ✗ | Login, returns token pair |
| GET | `/auth/me` | ✓ | Get current user profile |
| POST | `/auth/refresh` | ✗ | Refresh access token |
| POST | `/auth/logout` | ✓ | Blacklist current token |

### Tasks

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/tasks/` | ✓ | Create task |
| GET | `/tasks/` | ✓ | List tasks (paginated, filterable) |
| GET | `/tasks/{id}` | ✓ | Get task by ID (cached) |
| PATCH | `/tasks/{id}` | ✓ | Partial update |
| DELETE | `/tasks/{id}` | ✓ | Soft delete |

**Query params for `GET /tasks/`:**
- `page` (int, default 1)
- `page_size` (int, 1–100, default 20)
- `status` — `todo | in_progress | done | archived`
- `priority` — `low | medium | high | urgent`
- `search` — fulltext search on title + description

### Users (Admin only)

| Method | Endpoint | Auth | Role |
|--------|----------|------|------|
| PATCH | `/users/me` | ✓ | USER+ |
| GET | `/users/` | ✓ | ADMIN |
| GET | `/users/{id}` | ✓ | ADMIN |
| PATCH | `/users/{id}` | ✓ | ADMIN |
| DELETE | `/users/{id}` | ✓ | ADMIN |

### Response format

**Success:**
```json
{
  "id": "uuid",
  "title": "...",
  "status": "todo",
  "priority": "high",
  ...
}
```

**Error:**
```json
{
  "success": false,
  "error": "Validation failed",
  "detail": [{ "field": "body -> password", "message": "..." }],
  "status_code": 422
}
```

---

## Security Design

### JWT Token Strategy

```
Login → access_token (30min) + refresh_token (7 days)
         │
         ▼ used on every API call
Authorization: Bearer <access_token>
         │
         ▼ 401 received
Auto-refresh via Axios interceptor → POST /auth/refresh
         │
         ▼ on logout
access_token blacklisted in Redis with TTL = remaining token lifetime
```

- Tokens are **stateless JWTs** — no server DB hit on each request
- **Logout is instant** — Redis blacklist checked before every authenticated endpoint
- Tokens carry `sub` (user ID), `role`, `type` (access/refresh), `iat` (issued at)
- The `iat` + `sub` form a unique `jti` used as the Redis blacklist key

### Password Security

- `bcrypt` hashing via `passlib` — adaptive cost factor, resistant to GPU attacks
- Passwords never stored in plaintext or returned in any response
- Login errors return a generic "Invalid email or password" to prevent user enumeration

### Input Validation

- All inputs validated by Pydantic v2 before reaching service layer
- Username: regex `^[a-zA-Z0-9_]{3,50}$`
- Password: min 8 chars, must contain uppercase + digit
- Title: max 200 chars, stripped whitespace
- Description: max 5000 chars
- Search: max 100 chars, ILIKE query (parameterized, SQL injection safe)

### Other Protections

- Rate limiting: 60 req/min per IP (configurable)
- CORS: explicit `ALLOWED_ORIGINS` allowlist
- `X-Process-Time` header on every response for monitoring
- Soft delete: data retained for audit — no hard deletes

---

## Scalability Notes

### Current Architecture (Monolith)

Suitable for: 0–50k users, single region, single server.

### Horizontal Scaling Path

**1. Stateless API — scale immediately**

The FastAPI app is fully stateless (all state in Postgres + Redis). You can run N replicas behind a load balancer with zero config changes:

```
Load Balancer (Nginx / AWS ALB)
    ├── API Instance 1
    ├── API Instance 2
    └── API Instance N
         ↓ shared
    Neon PostgreSQL + Redis (Upstash)
```

**2. Caching layer (already implemented)**

- Individual task reads cached in Redis (TTL 2min)
- Cache busted on every write
- Next step: add cache for `list_tasks` with user-scoped keys

**3. Database connection pooling**

Currently using `NullPool` for Neon serverless compatibility. For dedicated Postgres, switch to `AsyncAdaptedQueuePool` with:
```python
pool_size=10, max_overflow=20, pool_pre_ping=True
```

**4. Async task queue (future)**

For email verification, webhooks, or long-running jobs — add **Celery + Redis** or **ARQ** (async Redis queue). The existing Redis client is already wired in.

**5. Microservices extraction**

Natural service boundaries for splitting if needed:
- `auth-service` — registration, login, token management
- `task-service` — CRUD, filtering, due date reminders
- `notification-service` — email, push, webhooks

Each service exposes its own `/api/v1/` and communicates via REST or a message broker (RabbitMQ / Kafka).

**6. Read replicas**

Neon supports read replicas. Route `SELECT` queries to the replica:
```python
read_engine = create_async_engine(READ_REPLICA_URL)
```

**7. Observability stack**

Production checklist:
- Structured JSON logs → shipped to **Datadog / Grafana Loki**
- Metrics → **Prometheus** (FastAPI has native `/metrics` support)
- Traces → **OpenTelemetry** with Jaeger
- Uptime → **UptimeRobot** pinging `/api/v1/health`

---

## Deployment

### Backend → Render

1. Create a new **Web Service** on [Render](https://render.com)
2. Set build command: `pip install -r requirements.txt && alembic upgrade head`
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables from `.env.example`

### Frontend → Vercel

```bash
cd frontend
npx vercel --prod
# Set NEXT_PUBLIC_API_URL to your Render backend URL
```

### Redis → Upstash

1. Create a free Redis database at [Upstash](https://upstash.com)
2. Copy the `REDIS_URL` (TLS format) into your Render environment variables

---

## Author

## Built by **Sahil Salap** — a passionate full-stack developer with a love for clean architecture and scalable design. Always eager to learn new technologies and solve complex problems.
## Email: sahilsalap75@gmail.com
## Phone: 8850306843
## GitHub: [github.com/sahildev109](https://github.com/sahildev109)
## LinkedIn: [linkedin.com/in/sahilsalap](https://www.linkedin.com/in/sahilsalap)
