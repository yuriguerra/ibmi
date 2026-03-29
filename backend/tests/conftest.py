"""Fixtures pytest: client FastAPI, sessão de banco para testes."""
import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app

# Configurar BD de teste (ex.: SQLite async ou Postgres de teste)
# TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
# engine = create_async_engine(TEST_DATABASE_URL, echo=False)
# AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Sessão de banco para testes (quando BD de teste estiver configurada)."""
    # async with AsyncSessionLocal() as session:
    #     async with engine.begin() as conn:
    #         await conn.run_sync(Base.metadata.create_all)
    #     yield session
    yield None  # placeholder até ter TEST_DATABASE_URL


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Client síncrono para testes de API."""
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Client assíncrono para testes de API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
