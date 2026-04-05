"""Testes básicos dos endpoints de estrutura eclesiástica."""
import pytest
from httpx import AsyncClient


# ─── Fixtures de autenticação ─────────────────────────────────────────────────

@pytest.fixture
async def admin_token(async_client: AsyncClient) -> str:
    """Retorna access token de um usuário ADMIN."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@ibmi.app", "password": "admin1234"},
    )
    assert response.status_code == 200, f"Login falhou: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


# ─── Igreja ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_criar_igreja_matriz(async_client: AsyncClient, admin_headers: dict):
    response = await async_client.post(
        "/api/v1/estrutura-eclesiastica/igrejas",
        json={"nome": "Igreja Sede", "tipo": "MATRIZ"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Igreja Sede"
    assert data["tipo"] == "MATRIZ"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_criar_congregacao_sem_mae_falha(async_client: AsyncClient, admin_headers: dict):
    response = await async_client.post(
        "/api/v1/estrutura-eclesiastica/igrejas",
        json={"nome": "Congregação Sem Mãe", "tipo": "CONGREGACAO"},
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert "igreja_mae_id" in response.json()["detail"]


@pytest.mark.asyncio
async def test_criar_congregacao_com_mae(async_client: AsyncClient, admin_headers: dict):
    # Cria matriz primeiro
    r_mae = await async_client.post(
        "/api/v1/estrutura-eclesiastica/igrejas",
        json={"nome": "Matriz Para Congregação", "tipo": "MATRIZ"},
        headers=admin_headers,
    )
    assert r_mae.status_code == 201
    mae_id = r_mae.json()["id"]

    response = await async_client.post(
        "/api/v1/estrutura-eclesiastica/igrejas",
        json={"nome": "Congregação Centro", "tipo": "CONGREGACAO", "igreja_mae_id": mae_id},
        headers=admin_headers,
    )
    assert response.status_code == 201
    assert response.json()["igreja_mae_id"] == mae_id


@pytest.mark.asyncio
async def test_listar_igrejas(async_client: AsyncClient, admin_headers: dict):
    response = await async_client.get(
        "/api/v1/estrutura-eclesiastica/igrejas",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_obter_igreja_inexistente(async_client: AsyncClient, admin_headers: dict):
    response = await async_client.get(
        "/api/v1/estrutura-eclesiastica/igrejas/99999",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_atualizar_igreja(async_client: AsyncClient, admin_headers: dict):
    r = await async_client.post(
        "/api/v1/estrutura-eclesiastica/igrejas",
        json={"nome": "Igreja Original", "tipo": "MATRIZ"},
        headers=admin_headers,
    )
    igreja_id = r.json()["id"]

    response = await async_client.patch(
        f"/api/v1/estrutura-eclesiastica/igrejas/{igreja_id}",
        json={"nome": "Igreja Atualizada"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["nome"] == "Igreja Atualizada"


@pytest.mark.asyncio
async def test_deletar_igreja(async_client: AsyncClient, admin_headers: dict):
    r = await async_client.post(
        "/api/v1/estrutura-eclesiastica/igrejas",
        json={"nome": "Igreja Para Deletar", "tipo": "MATRIZ"},
        headers=admin_headers,
    )
    igreja_id = r.json()["id"]

    response = await async_client.delete(
        f"/api/v1/estrutura-eclesiastica/igrejas/{igreja_id}",
        headers=admin_headers,
    )
    assert response.status_code == 204

    # Confirma remoção
    r_get = await async_client.get(
        f"/api/v1/estrutura-eclesiastica/igrejas/{igreja_id}",
        headers=admin_headers,
    )
    assert r_get.status_code == 404


@pytest.mark.asyncio
async def test_criar_igreja_sem_autenticacao(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/estrutura-eclesiastica/igrejas",
        json={"nome": "Igreja Sem Auth", "tipo": "MATRIZ"},
    )
    assert response.status_code == 401


# ─── Departamento ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_criar_departamento(async_client: AsyncClient, admin_headers: dict):
    r = await async_client.post(
        "/api/v1/estrutura-eclesiastica/igrejas",
        json={"nome": "Igreja Dep Test", "tipo": "MATRIZ"},
        headers=admin_headers,
    )
    igreja_id = r.json()["id"]

    response = await async_client.post(
        "/api/v1/estrutura-eclesiastica/departamentos",
        json={"nome": "Jovens", "igreja_id": igreja_id},
        headers=admin_headers,
    )
    assert response.status_code == 201
    assert response.json()["nome"] == "Jovens"
    assert response.json()["igreja_id"] == igreja_id


@pytest.mark.asyncio
async def test_criar_departamento_igreja_inexistente(async_client: AsyncClient, admin_headers: dict):
    response = await async_client.post(
        "/api/v1/estrutura-eclesiastica/departamentos",
        json={"nome": "Jovens", "igreja_id": 99999},
        headers=admin_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_listar_departamentos_por_igreja(async_client: AsyncClient, admin_headers: dict):
    r = await async_client.post(
        "/api/v1/estrutura-eclesiastica/igrejas",
        json={"nome": "Igreja Lista Dep", "tipo": "MATRIZ"},
        headers=admin_headers,
    )
    igreja_id = r.json()["id"]

    await async_client.post(
        "/api/v1/estrutura-eclesiastica/departamentos",
        json={"nome": "Louvor", "igreja_id": igreja_id},
        headers=admin_headers,
    )

    response = await async_client.get(
        f"/api/v1/estrutura-eclesiastica/igrejas/{igreja_id}/departamentos",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_deletar_departamento(async_client: AsyncClient, admin_headers: dict):
    r_igreja = await async_client.post(
        "/api/v1/estrutura-eclesiastica/igrejas",
        json={"nome": "Igreja Del Dep", "tipo": "MATRIZ"},
        headers=admin_headers,
    )
    r_dep = await async_client.post(
        "/api/v1/estrutura-eclesiastica/departamentos",
        json={"nome": "Infância", "igreja_id": r_igreja.json()["id"]},
        headers=admin_headers,
    )
    dep_id = r_dep.json()["id"]

    response = await async_client.delete(
        f"/api/v1/estrutura-eclesiastica/departamentos/{dep_id}",
        headers=admin_headers,
    )
    assert response.status_code == 204
