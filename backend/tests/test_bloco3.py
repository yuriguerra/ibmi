"""Testes básicos: estrutura eclesiástica e pessoas & ministérios."""
import pytest
from httpx import AsyncClient


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
async def admin_headers(async_client: AsyncClient) -> dict:
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@ibmi.app", "password": "admin1234"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
async def igreja_id(async_client: AsyncClient, admin_headers: dict) -> int:
    r = await async_client.post(
        "/api/v1/estrutura-eclesiastica/igrejas",
        json={"nome": "Igreja Fixture", "tipo": "MATRIZ"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    return r.json()["id"]


@pytest.fixture
async def departamento_id(
    async_client: AsyncClient, admin_headers: dict, igreja_id: int
) -> int:
    r = await async_client.post(
        "/api/v1/estrutura-eclesiastica/departamentos",
        json={"nome": "Jovens Fixture", "igreja_id": igreja_id},
        headers=admin_headers,
    )
    assert r.status_code == 201
    return r.json()["id"]


@pytest.fixture
async def ministerio_id(
    async_client: AsyncClient, admin_headers: dict, igreja_id: int
) -> int:
    r = await async_client.post(
        "/api/v1/pessoas-ministerios/ministerios",
        json={"nome": "Louvor Fixture", "igreja_id": igreja_id},
        headers=admin_headers,
    )
    assert r.status_code == 201
    return r.json()["id"]


# ─── Igreja ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_criar_igreja_matriz(async_client: AsyncClient, admin_headers: dict):
    r = await async_client.post(
        "/api/v1/estrutura-eclesiastica/igrejas",
        json={"nome": "Igreja Sede", "tipo": "MATRIZ"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.json()["tipo"] == "MATRIZ"


@pytest.mark.asyncio
async def test_criar_congregacao_sem_mae_falha(async_client: AsyncClient, admin_headers: dict):
    r = await async_client.post(
        "/api/v1/estrutura-eclesiastica/igrejas",
        json={"nome": "Congregação Órfã", "tipo": "CONGREGACAO"},
        headers=admin_headers,
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_criar_congregacao_com_mae(
    async_client: AsyncClient, admin_headers: dict, igreja_id: int
):
    r = await async_client.post(
        "/api/v1/estrutura-eclesiastica/igrejas",
        json={"nome": "Congregação Centro", "tipo": "CONGREGACAO", "igreja_mae_id": igreja_id},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.json()["igreja_mae_id"] == igreja_id


@pytest.mark.asyncio
async def test_soft_delete_igreja(
    async_client: AsyncClient, admin_headers: dict, igreja_id: int
):
    # Soft delete
    r = await async_client.delete(
        f"/api/v1/estrutura-eclesiastica/igrejas/{igreja_id}",
        headers=admin_headers,
    )
    assert r.status_code == 204

    # Não aparece mais na listagem
    r_get = await async_client.get(
        f"/api/v1/estrutura-eclesiastica/igrejas/{igreja_id}",
        headers=admin_headers,
    )
    assert r_get.status_code == 404


@pytest.mark.asyncio
async def test_hard_delete_igreja(async_client: AsyncClient, admin_headers: dict):
    r_create = await async_client.post(
        "/api/v1/estrutura-eclesiastica/igrejas",
        json={"nome": "Igreja LGPD", "tipo": "MATRIZ"},
        headers=admin_headers,
    )
    id_ = r_create.json()["id"]

    r = await async_client.delete(
        f"/api/v1/estrutura-eclesiastica/igrejas/{id_}/permanente",
        headers=admin_headers,
    )
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_listar_igrejas(async_client: AsyncClient, admin_headers: dict, igreja_id: int):
    r = await async_client.get(
        "/api/v1/estrutura-eclesiastica/igrejas",
        headers=admin_headers,
    )
    assert r.status_code == 200
    ids = [i["id"] for i in r.json()]
    assert igreja_id in ids


# ─── Departamento ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_criar_departamento(
    async_client: AsyncClient, admin_headers: dict, igreja_id: int
):
    r = await async_client.post(
        "/api/v1/estrutura-eclesiastica/departamentos",
        json={"nome": "Louvor", "igreja_id": igreja_id},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.json()["nome"] == "Louvor"


@pytest.mark.asyncio
async def test_soft_delete_departamento(
    async_client: AsyncClient, admin_headers: dict, departamento_id: int
):
    r = await async_client.delete(
        f"/api/v1/estrutura-eclesiastica/departamentos/{departamento_id}",
        headers=admin_headers,
    )
    assert r.status_code == 204

    r_get = await async_client.get(
        f"/api/v1/estrutura-eclesiastica/departamentos/{departamento_id}",
        headers=admin_headers,
    )
    assert r_get.status_code == 404


# ─── Ministério ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_criar_ministerio(
    async_client: AsyncClient, admin_headers: dict, igreja_id: int
):
    r = await async_client.post(
        "/api/v1/pessoas-ministerios/ministerios",
        json={"nome": "Intercessão", "igreja_id": igreja_id},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.json()["nome"] == "Intercessão"


@pytest.mark.asyncio
async def test_soft_delete_ministerio(
    async_client: AsyncClient, admin_headers: dict, ministerio_id: int
):
    r = await async_client.delete(
        f"/api/v1/pessoas-ministerios/ministerios/{ministerio_id}",
        headers=admin_headers,
    )
    assert r.status_code == 204

    r_get = await async_client.get(
        f"/api/v1/pessoas-ministerios/ministerios/{ministerio_id}",
        headers=admin_headers,
    )
    assert r_get.status_code == 404


# ─── Membro ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_criar_membro(
    async_client: AsyncClient, admin_headers: dict, igreja_id: int
):
    r = await async_client.post(
        "/api/v1/pessoas-ministerios/membros",
        json={
            "nome_completo": "João da Silva",
            "email": "joao@ibmi.app",
            "status": "ATIVO",
            "igreja_principal_id": igreja_id,
        },
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.json()["nome_completo"] == "João da Silva"


@pytest.mark.asyncio
async def test_vincular_membro_departamento(
    async_client: AsyncClient, admin_headers: dict, igreja_id: int, departamento_id: int
):
    r_m = await async_client.post(
        "/api/v1/pessoas-ministerios/membros",
        json={"nome_completo": "Maria Souza", "status": "ATIVO", "igreja_principal_id": igreja_id},
        headers=admin_headers,
    )
    membro_id = r_m.json()["id"]

    r = await async_client.post(
        f"/api/v1/pessoas-ministerios/membros/{membro_id}/departamentos",
        json={"departamento_id": departamento_id},
        headers=admin_headers,
    )
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_vincular_membro_ministerio(
    async_client: AsyncClient, admin_headers: dict, igreja_id: int, ministerio_id: int
):
    r_m = await async_client.post(
        "/api/v1/pessoas-ministerios/membros",
        json={"nome_completo": "Pedro Costa", "status": "ATIVO", "igreja_principal_id": igreja_id},
        headers=admin_headers,
    )
    membro_id = r_m.json()["id"]

    r = await async_client.post(
        f"/api/v1/pessoas-ministerios/membros/{membro_id}/ministerios",
        json={"ministerio_id": ministerio_id, "funcao": "Músico"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.json()["funcao"] == "Músico"


@pytest.mark.asyncio
async def test_soft_delete_membro(
    async_client: AsyncClient, admin_headers: dict, igreja_id: int
):
    r_m = await async_client.post(
        "/api/v1/pessoas-ministerios/membros",
        json={"nome_completo": "Deletar Membro", "status": "ATIVO"},
        headers=admin_headers,
    )
    membro_id = r_m.json()["id"]

    r = await async_client.delete(
        f"/api/v1/pessoas-ministerios/membros/{membro_id}",
        headers=admin_headers,
    )
    assert r.status_code == 204

    r_get = await async_client.get(
        f"/api/v1/pessoas-ministerios/membros/{membro_id}",
        headers=admin_headers,
    )
    assert r_get.status_code == 404
