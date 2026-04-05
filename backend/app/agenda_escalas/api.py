"""Rotas do contexto Agenda & Escalas."""
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agenda_escalas.schemas.agenda import (
    CopiarEscalaRequest,
    EscalaCreate,
    EscalaResponse,
    EscalaUpdate,
    EventoCreate,
    EventoResponse,
    EventoUpdate,
    OcorrenciaOverride,
    OcorrenciaResponse,
    TipoEventoCreate,
    TipoEventoResponse,
    TipoEventoUpdate,
)
from app.agenda_escalas.services.agenda_service import (
    agenda_service,
    escala_service,
    evento_service,
    ocorrencia_service,
    tipo_evento_service,
)
from app.api.deps import AdminUser, CurrentUser
from app.core.database import get_db
from datetime import datetime

router = APIRouter()
DB = Annotated[AsyncSession, Depends(get_db)]


# ─── Tipos de Evento ──────────────────────────────────────────────────────────

@router.get("/tipos-evento", response_model=List[TipoEventoResponse])
async def listar_tipos_evento(
    _: CurrentUser,
    db: DB,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> List[TipoEventoResponse]:
    return await tipo_evento_service.listar(db, limit=limit, offset=offset)


@router.get("/tipos-evento/{tipo_id}", response_model=TipoEventoResponse)
async def obter_tipo_evento(tipo_id: int, _: CurrentUser, db: DB) -> TipoEventoResponse:
    tipo = await tipo_evento_service.obter(db, tipo_id)
    if not tipo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de evento não encontrado.")
    return tipo


@router.post("/tipos-evento", response_model=TipoEventoResponse, status_code=status.HTTP_201_CREATED)
async def criar_tipo_evento(data: TipoEventoCreate, _: AdminUser, db: DB) -> TipoEventoResponse:
    return await tipo_evento_service.criar(db, data)


@router.patch("/tipos-evento/{tipo_id}", response_model=TipoEventoResponse)
async def atualizar_tipo_evento(
    tipo_id: int, data: TipoEventoUpdate, _: AdminUser, db: DB
) -> TipoEventoResponse:
    tipo = await tipo_evento_service.atualizar(db, tipo_id, data)
    if not tipo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de evento não encontrado.")
    return tipo


@router.delete("/tipos-evento/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_tipo_evento(tipo_id: int, _: AdminUser, db: DB) -> None:
    if not await tipo_evento_service.deletar(db, tipo_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de evento não encontrado.")


# ─── Eventos ──────────────────────────────────────────────────────────────────

@router.get("/eventos/{evento_id}", response_model=EventoResponse)
async def obter_evento(evento_id: int, _: CurrentUser, db: DB) -> EventoResponse:
    evento = await evento_service.obter(db, evento_id)
    if not evento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado.")
    return evento


@router.post("/eventos", response_model=EventoResponse, status_code=status.HTTP_201_CREATED)
async def criar_evento(data: EventoCreate, _: AdminUser, db: DB) -> EventoResponse:
    """
    Cria evento mestre.

    Se `recorrencia` for informado, gera automaticamente as ocorrências.
    Caso contrário, cria uma única ocorrência.
    """
    try:
        return await evento_service.criar(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/eventos/{evento_id}", response_model=EventoResponse)
async def atualizar_evento(
    evento_id: int, data: EventoUpdate, _: AdminUser, db: DB
) -> EventoResponse:
    evento = await evento_service.atualizar(db, evento_id, data)
    if not evento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado.")
    return evento


@router.delete("/eventos/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_evento(evento_id: int, _: AdminUser, db: DB) -> None:
    if not await evento_service.deletar(db, evento_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado.")


# ─── Ocorrências ──────────────────────────────────────────────────────────────

@router.get("/eventos/{evento_id}/ocorrencias", response_model=List[OcorrenciaResponse])
async def listar_ocorrencias(
    evento_id: int,
    _: CurrentUser,
    db: DB,
    incluir_cancelados: bool = Query(False),
) -> List[OcorrenciaResponse]:
    return await ocorrencia_service.listar_por_evento(
        db, evento_id, incluir_cancelados=incluir_cancelados
    )


@router.patch("/ocorrencias/{ocorrencia_id}", response_model=OcorrenciaResponse)
async def aplicar_override_ocorrencia(
    ocorrencia_id: int,
    data: OcorrenciaOverride,
    _: AdminUser,
    db: DB,
) -> OcorrenciaResponse:
    """Aplica ajuste pontual (horário diferente, cancelamento, nota) a uma ocorrência."""
    oc = await ocorrencia_service.aplicar_override(db, ocorrencia_id, data)
    if not oc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ocorrência não encontrada.")
    return oc


# ─── Escala ───────────────────────────────────────────────────────────────────

@router.get("/ocorrencias/{ocorrencia_id}/escala", response_model=List[EscalaResponse])
async def listar_escala(ocorrencia_id: int, _: CurrentUser, db: DB) -> List[EscalaResponse]:
    return await escala_service.listar(db, ocorrencia_id)


@router.post(
    "/ocorrencias/{ocorrencia_id}/escala",
    response_model=EscalaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def criar_escala(
    ocorrencia_id: int, data: EscalaCreate, _: AdminUser, db: DB
) -> EscalaResponse:
    oc = await ocorrencia_service.obter(db, ocorrencia_id)
    if not oc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ocorrência não encontrada.")
    return await escala_service.criar(db, ocorrencia_id, data)


@router.patch("/escala/{escala_id}", response_model=EscalaResponse)
async def atualizar_escala(
    escala_id: int, data: EscalaUpdate, _: AdminUser, db: DB
) -> EscalaResponse:
    escala = await escala_service.atualizar(db, escala_id, data)
    if not escala:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item de escala não encontrado.")
    return escala


@router.delete("/escala/{escala_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_escala(escala_id: int, _: AdminUser, db: DB) -> None:
    if not await escala_service.deletar(db, escala_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item de escala não encontrado.")


@router.post("/escala/copiar", status_code=status.HTTP_200_OK)
async def copiar_escala(
    data: CopiarEscalaRequest, _: AdminUser, db: DB
) -> dict:
    """Copia escala de uma ocorrência para outras. Retorna total de itens copiados."""
    total = await escala_service.copiar(db, data)
    return {"copiados": total}


# ─── Agenda ───────────────────────────────────────────────────────────────────

@router.get("/agenda", response_model=List[OcorrenciaResponse])
async def consultar_agenda(
    current_user: CurrentUser,
    db: DB,
    data_inicio: datetime = Query(...),
    data_fim: datetime = Query(...),
    igreja_id: Optional[int] = Query(None),
    membro_id: Optional[int] = Query(None),
    departamento_id: Optional[int] = Query(None),
    ministerio_id: Optional[int] = Query(None),
    tipo_evento_id: Optional[int] = Query(None),
    incluir_cancelados: bool = Query(False),
) -> List[OcorrenciaResponse]:
    """
    Retorna ocorrências no intervalo informado com filtros e regras de visibilidade.

    - ADMIN vê todos os eventos da organização.
    - MEMBRO vê apenas eventos visíveis conforme seu perfil (GERAL + seus departamentos/ministérios/convites).
    """
    return await agenda_service.consultar(
        db,
        usuario=current_user,
        data_inicio=data_inicio,
        data_fim=data_fim,
        igreja_id=igreja_id,
        membro_id=membro_id,
        departamento_id=departamento_id,
        ministerio_id=ministerio_id,
        tipo_evento_id=tipo_evento_id,
        incluir_cancelados=incluir_cancelados,
    )
