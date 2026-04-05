"""
Fixtures pytest para o backend IBMI.

Banco de teste: PostgreSQL real (via variável TEST_DATABASE_URL no .env).
Cada sessão de teste roda dentro de uma transação revertida ao fim (rollback).
"""
import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from typing import Optional

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app

# ─── URL do banco de teste ────────────────────────────────────────────────────
# Defina TEST_DATABASE_URL no .env ou como variável de ambiente.
# Exemplo: postgresql+asyncpg://ibmi:ibmi@localhost:5432/ibmi_test
TEST_DATABASE_URL: Optional[str] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://ibmi:ibmi@localhost:5432/ibmi_test",
)


# ─── Engine e sessão de teste ─────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Event loop compartilhado por toda a sessão de testes."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_engine():
    """Engine async para o banco de teste. Criado uma vez por sessão."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    return engine


@pytest_asyncio.fixture(scope="session", autouse=True)
async def criar_tabelas(test_engine):
    """
    Cria todas as tabelas no banco de teste antes dos testes
    e as remove ao final da sessão.
    """
    # Importa todos os modelos para registrar no metadata
    import app.shared.all_models  # noqa: F401

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Sessão de banco isolada por teste via savepoint (ROLLBACK ao fim).

    Padrão: transação externa + savepoint interno.
    A transação externa nunca faz commit — garante isolamento entre testes.
    """
    async with test_engine.connect() as conn:
        await conn.begin()
        session_factory = async_sessionmaker(
            bind=conn,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        async with session_factory() as session:
            yield session
        await conn.rollback()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP assíncrono com override de get_db apontando para db_session.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ─── Factories de dados ───────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def admin_usuario(db_session: AsyncSession):
    """Cria e retorna um usuário ADMIN para uso nos testes."""
    from app.auth.models.usuario import Usuario
    from app.core.security import get_password_hash

    usuario = Usuario(
        email="admin@teste.com",
        hashed_password=get_password_hash("Senha@123"),
        perfil="ADMIN",
        ativo=True,
    )
    db_session.add(usuario)
    await db_session.flush()
    await db_session.refresh(usuario)
    return usuario


@pytest_asyncio.fixture
async def admin_token(async_client: AsyncClient, admin_usuario) -> str:
    """Retorna access token JWT do usuário ADMIN."""
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@teste.com", "password": "Senha@123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(admin_token: str) -> dict:
    """Headers de autorização prontos para uso nos testes."""
    return {"Authorization": f"Bearer {admin_token}"}
