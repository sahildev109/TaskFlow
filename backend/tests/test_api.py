import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db.session import Base, get_db
from app.core.config import settings

# Use in-memory SQLite for tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Auth Tests ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPass1",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["role"] == "user"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "username": "dup1", "password": "TestPass1"},
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "username": "dup2", "password": "TestPass1"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "username": "loginuser", "password": "TestPass1"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "TestPass1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "WrongPass1"},
    )
    assert response.status_code == 401


# ── Task Tests ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_task(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "task@example.com", "username": "taskuser", "password": "TestPass1"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "task@example.com", "password": "TestPass1"},
    )
    token = login.json()["access_token"]

    response = await client.post(
        "/api/v1/tasks/",
        json={"title": "My first task", "priority": "high"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["title"] == "My first task"


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "task@example.com", "password": "TestPass1"},
    )
    token = login.json()["access_token"]

    response = await client.get(
        "/api/v1/tasks/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "tasks" in response.json()


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    response = await client.get("/api/v1/tasks/")
    assert response.status_code == 403
