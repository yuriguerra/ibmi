"""Rotas do contexto Pessoas & Ministérios."""
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser, CurrentUser
from app.core.database import get_db
from app.pessoas_ministerios.schemas.pessoas import (
    MembroCreate,
    MembroDepartamentoCreate,
    MembroMinisterioCreate,
    MembroMinisterioResponse,
    MembroResponse,
    MembroUpdate,
    MinisterioCreate,
    MinisterioResponse,
    MinisterioUpdate,
)
from app.pessoas_ministerios.services.pessoas_service import (
    membro_service,
    ministerio_service,
)

router = APIRouter()
DB = Annotated[AsyncSession, Depends(get_db)]


# ─── Ministérios ──────────────────────────────────────────────────────────────

@router.get("/ministerios", response_model=List[MinisterioResponse])
async def listar_ministerios(
    _: CurrentUser,
    db: DB,
    igreja_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> List[MinisterioResponse]:
    """Lista ministérios ativos. Filtrável por igreja. Requer autenticação."""
    return await ministerio_service.listar(db, igreja_id=igreja_id, limit=limit, offset=offset)


@router.get("/ministerios/{ministerio_id}", response_model=MinisterioResponse)
async def obter_ministerio(
    ministerio_id: int,
    _: CurrentUser,
    db: DB,
) -> MinisterioResponse:
    m = await ministerio_service.obter(db, ministerio_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ministério não encontrado.")
    return m


@router.post("/ministerios", response_model=MinisterioResponse, status_code=status.HTTP_201_CREATED)
async def criar_ministerio(
    data: MinisterioCreate,
    _: AdminUser,
    db: DB,
) -> MinisterioResponse:
    """Cria ministério vinculado a uma igreja. Restrito a ADMIN."""
    try:
        return await ministerio_service.criar(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/ministerios/{ministerio_id}", response_model=MinisterioResponse)
async def atualizar_ministerio(
    ministerio_id: int,
    data: MinisterioUpdate,
    _: AdminUser,
    db: DB,
) -> MinisterioResponse:
    m = await ministerio_service.atualizar(db, ministerio_id, data)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ministério não encontrado.")
    return m


@router.delete("/ministerios/{ministerio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_ministerio(
    ministerio_id: int,
    _: AdminUser,
    db: DB,
) -> None:
    """Soft delete. Restrito a ADMIN."""
    if not await ministerio_service.deletar(db, ministerio_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ministério não encontrado.")


@router.delete(
    "/ministerios/{ministerio_id}/permanente",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover ministério permanentemente (LGPD)",
)
async def deletar_ministerio_permanente(
    ministerio_id: int,
    _: AdminUser,
    db: DB,
) -> None:
    """Hard delete (LGPD). Restrito a ADMIN."""
    if not await ministerio_service.deletar_permanente(db, ministerio_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ministério não encontrado.")


# ─── Membros ──────────────────────────────────────────────────────────────────

@router.get("/membros", response_model=List[MembroResponse])
async def listar_membros(
    _: CurrentUser,
    db: DB,
    igreja_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> List[MembroResponse]:
    """Lista membros ativos. Filtrável por igreja e status. Requer autenticação."""
    return await membro_service.listar(
        db, igreja_id=igreja_id, status=status, limit=limit, offset=offset
    )


@router.get("/membros/{membro_id}", response_model=MembroResponse)
async def obter_membro(
    membro_id: int,
    _: CurrentUser,
    db: DB,
) -> MembroResponse:
    m = await membro_service.obter(db, membro_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro não encontrado.")
    return m


@router.post("/membros", response_model=MembroResponse, status_code=status.HTTP_201_CREATED)
async def criar_membro(
    data: MembroCreate,
    _: AdminUser,
    db: DB,
) -> MembroResponse:
    """Cria novo membro. Restrito a ADMIN."""
    return await membro_service.criar(db, data)


@router.patch("/membros/{membro_id}", response_model=MembroResponse)
async def atualizar_membro(
    membro_id: int,
    data: MembroUpdate,
    _: AdminUser,
    db: DB,
) -> MembroResponse:
    m = await membro_service.atualizar(db, membro_id, data)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro não encontrado.")
    return m


@router.delete("/membros/{membro_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_membro(
    membro_id: int,
    _: AdminUser,
    db: DB,
) -> None:
    """Soft delete. Restrito a ADMIN."""
    if not await membro_service.deletar(db, membro_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro não encontrado.")


@router.delete(
    "/membros/{membro_id}/permanente",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover membro permanentemente (LGPD)",
)
async def deletar_membro_permanente(
    membro_id: int,
    _: AdminUser,
    db: DB,
) -> None:
    """Hard delete (LGPD). Restrito a ADMIN."""
    if not await membro_service.deletar_permanente(db, membro_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro não encontrado.")


# ─── Vínculos Membro ↔ Departamento ──────────────────────────────────────────

@router.post(
    "/membros/{membro_id}/departamentos",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def adicionar_departamento(
    membro_id: int,
    data: MembroDepartamentoCreate,
    _: AdminUser,
    db: DB,
) -> None:
    """Vincula membro a um departamento. Restrito a ADMIN."""
    try:
        await membro_service.adicionar_departamento(db, membro_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/membros/{membro_id}/departamentos/{departamento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remover_departamento(
    membro_id: int,
    departamento_id: int,
    _: AdminUser,
    db: DB,
) -> None:
    """Remove vínculo membro-departamento. Restrito a ADMIN."""
    if not await membro_service.remover_departamento(db, membro_id, departamento_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vínculo não encontrado.")


# ─── Vínculos Membro ↔ Ministério ────────────────────────────────────────────

@router.post(
    "/membros/{membro_id}/ministerios",
    response_model=MembroMinisterioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def adicionar_ministerio(
    membro_id: int,
    data: MembroMinisterioCreate,
    _: AdminUser,
    db: DB,
) -> MembroMinisterioResponse:
    """Vincula membro a um ministério (com função opcional). Restrito a ADMIN."""
    try:
        return await membro_service.adicionar_ministerio(db, membro_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/membros/{membro_id}/ministerios/{ministerio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remover_ministerio(
    membro_id: int,
    ministerio_id: int,
    _: AdminUser,
    db: DB,
) -> None:
    """Remove vínculo membro-ministério. Restrito a ADMIN."""
    if not await membro_service.remover_ministerio(db, membro_id, ministerio_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vínculo não encontrado.")
