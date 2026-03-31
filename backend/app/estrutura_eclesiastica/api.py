"""Rotas do contexto Estrutura Eclesiástica: igrejas e departamentos."""
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser, CurrentUser
from app.core.database import get_db
from app.estrutura_eclesiastica.schemas.estrutura import (
    DepartamentoCreate,
    DepartamentoResponse,
    DepartamentoUpdate,
    IgrejaCreate,
    IgrejaResponse,
    IgrejaUpdate,
)
from app.estrutura_eclesiastica.services.estrutura_service import igreja_service

router = APIRouter()

DB = Annotated[AsyncSession, Depends(get_db)]


# ─── Igrejas ──────────────────────────────────────────────────────────────────

@router.get("/igrejas", response_model=List[IgrejaResponse])
async def listar_igrejas(
    _: CurrentUser,
    db: DB,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> List[IgrejaResponse]:
    """Lista todas as igrejas/congregações. Requer autenticação."""
    return await igreja_service.listar(db, limit=limit, offset=offset)


@router.get("/igrejas/{igreja_id}", response_model=IgrejaResponse)
async def obter_igreja(
    igreja_id: int,
    _: CurrentUser,
    db: DB,
) -> IgrejaResponse:
    """Retorna uma igreja pelo ID."""
    igreja = await igreja_service.obter(db, igreja_id)
    if not igreja:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Igreja não encontrada.")
    return igreja


@router.post("/igrejas", response_model=IgrejaResponse, status_code=status.HTTP_201_CREATED)
async def criar_igreja(
    data: IgrejaCreate,
    _: AdminUser,
    db: DB,
) -> IgrejaResponse:
    """Cria uma nova igreja ou congregação. Restrito a ADMIN."""
    try:
        return await igreja_service.criar(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/igrejas/{igreja_id}", response_model=IgrejaResponse)
async def atualizar_igreja(
    igreja_id: int,
    data: IgrejaUpdate,
    _: AdminUser,
    db: DB,
) -> IgrejaResponse:
    """Atualiza parcialmente uma igreja. Restrito a ADMIN."""
    try:
        igreja = await igreja_service.atualizar(db, igreja_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not igreja:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Igreja não encontrada.")
    return igreja


@router.delete("/igrejas/{igreja_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_igreja(
    igreja_id: int,
    _: AdminUser,
    db: DB,
) -> None:
    """Remove uma igreja. Restrito a ADMIN."""
    deletado = await igreja_service.deletar(db, igreja_id)
    if not deletado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Igreja não encontrada.")


# ─── Departamentos ────────────────────────────────────────────────────────────

@router.get("/igrejas/{igreja_id}/departamentos", response_model=List[DepartamentoResponse])
async def listar_departamentos(
    igreja_id: int,
    _: CurrentUser,
    db: DB,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> List[DepartamentoResponse]:
    """Lista departamentos de uma igreja. Requer autenticação."""
    igreja = await igreja_service.obter(db, igreja_id)
    if not igreja:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Igreja não encontrada.")
    return await igreja_service.listar_departamentos(db, igreja_id, limit=limit, offset=offset)


@router.get("/departamentos/{departamento_id}", response_model=DepartamentoResponse)
async def obter_departamento(
    departamento_id: int,
    _: CurrentUser,
    db: DB,
) -> DepartamentoResponse:
    """Retorna um departamento pelo ID."""
    dep = await igreja_service.obter_departamento(db, departamento_id)
    if not dep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departamento não encontrado.")
    return dep


@router.post("/departamentos", response_model=DepartamentoResponse, status_code=status.HTTP_201_CREATED)
async def criar_departamento(
    data: DepartamentoCreate,
    _: AdminUser,
    db: DB,
) -> DepartamentoResponse:
    """Cria um departamento vinculado a uma igreja. Restrito a ADMIN."""
    try:
        return await igreja_service.criar_departamento(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/departamentos/{departamento_id}", response_model=DepartamentoResponse)
async def atualizar_departamento(
    departamento_id: int,
    data: DepartamentoUpdate,
    _: AdminUser,
    db: DB,
) -> DepartamentoResponse:
    """Atualiza parcialmente um departamento. Restrito a ADMIN."""
    dep = await igreja_service.atualizar_departamento(db, departamento_id, data)
    if not dep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departamento não encontrado.")
    return dep


@router.delete("/departamentos/{departamento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_departamento(
    departamento_id: int,
    _: AdminUser,
    db: DB,
) -> None:
    """Remove um departamento. Restrito a ADMIN."""
    deletado = await igreja_service.deletar_departamento(db, departamento_id)
    if not deletado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departamento não encontrado.")
