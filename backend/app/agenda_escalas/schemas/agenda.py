"""Schemas Pydantic para o contexto Agenda & Escalas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator


# ─── Tipo de Evento ───────────────────────────────────────────────────────────

class TipoEventoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    cor: Optional[str] = None


class TipoEventoCreate(TipoEventoBase):
    pass


class TipoEventoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    cor: Optional[str] = None


class TipoEventoResponse(TipoEventoBase):
    id: int

    model_config = {"from_attributes": True}


# ─── Recorrência ──────────────────────────────────────────────────────────────

class RecorrenciaCreate(BaseModel):
    frequencia: str  # DAILY | WEEKLY | MONTHLY
    intervalo: int = 1
    dias_semana: Optional[List[int]] = None   # 0=Dom…6=Sáb
    dias_mes: Optional[List[int]] = None      # 1-31
    posicao_na_semana: Optional[int] = None   # 1=primeiro, -1=último
    dia_semana_posicao: Optional[int] = None  # 0-6
    data_fim: Optional[datetime] = None
    ocorrencias_max: Optional[int] = None

    @field_validator("frequencia")
    @classmethod
    def frequencia_valida(cls, v: str) -> str:
        if v not in {"DAILY", "WEEKLY", "MONTHLY"}:
            raise ValueError("frequencia deve ser DAILY, WEEKLY ou MONTHLY")
        return v


class RecorrenciaResponse(RecorrenciaCreate):
    evento_id: int

    model_config = {"from_attributes": True}


# ─── Evento (mestre) ──────────────────────────────────────────────────────────

class EventoCreate(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    local: Optional[str] = None
    visibilidade: str = "GERAL"
    data_hora_inicio: datetime
    data_hora_fim: datetime
    igreja_id: int
    tipo_evento_id: Optional[int] = None
    recorrencia: Optional[RecorrenciaCreate] = None
    # IDs para tabelas de visibilidade restrita
    departamento_ids: Optional[List[int]] = None
    ministerio_ids: Optional[List[int]] = None
    membro_ids: Optional[List[int]] = None

    @field_validator("visibilidade")
    @classmethod
    def visibilidade_valida(cls, v: str) -> str:
        permitidos = {"GERAL", "POR_DEPARTAMENTO", "POR_MINISTERIO", "POR_MEMBRO"}
        if v not in permitidos:
            raise ValueError(f"visibilidade deve ser um de: {permitidos}")
        return v


class EventoUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    local: Optional[str] = None
    visibilidade: Optional[str] = None
    data_hora_inicio: Optional[datetime] = None
    data_hora_fim: Optional[datetime] = None
    tipo_evento_id: Optional[int] = None
    departamento_ids: Optional[List[int]] = None
    ministerio_ids: Optional[List[int]] = None
    membro_ids: Optional[List[int]] = None


class EventoResponse(BaseModel):
    id: int
    titulo: str
    descricao: Optional[str]
    local: Optional[str]
    visibilidade: str
    e_recorrente: bool
    data_hora_inicio: datetime
    data_hora_fim: datetime
    igreja_id: int
    tipo_evento_id: Optional[int]
    recorrencia: Optional[RecorrenciaResponse] = None

    model_config = {"from_attributes": True}


# ─── Ocorrência ───────────────────────────────────────────────────────────────

class OcorrenciaOverride(BaseModel):
    """Ajuste pontual em uma ocorrência individual."""
    data_hora_inicio: Optional[datetime] = None
    data_hora_fim: Optional[datetime] = None
    cancelado: Optional[bool] = None
    nota_ocorrencia: Optional[str] = None


class OcorrenciaResponse(BaseModel):
    id: int
    evento_id: int
    data_hora_inicio: datetime
    data_hora_fim: datetime
    cancelado: bool
    nota_ocorrencia: Optional[str]

    model_config = {"from_attributes": True}


# ─── Escala de Ministério ─────────────────────────────────────────────────────

class EscalaCreate(BaseModel):
    ministerio_id: int
    membro_id: int
    papel: Optional[str] = None
    status: str = "PENDENTE"
    observacoes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def status_valido(cls, v: str) -> str:
        if v not in {"PENDENTE", "CONFIRMADO", "CANCELADO", "SUBSTITUTO"}:
            raise ValueError("status inválido")
        return v


class EscalaUpdate(BaseModel):
    papel: Optional[str] = None
    status: Optional[str] = None
    observacoes: Optional[str] = None


class EscalaResponse(BaseModel):
    id: int
    evento_ocorrencia_id: int
    ministerio_id: int
    membro_id: int
    papel: Optional[str]
    status: str
    observacoes: Optional[str]

    model_config = {"from_attributes": True}


class CopiarEscalaRequest(BaseModel):
    """Copia escala de uma ocorrência para outras."""
    ocorrencia_origem_id: int
    ocorrencia_destino_ids: List[int]


# ─── Agenda (consulta com filtros) ────────────────────────────────────────────

class AgendaFiltros(BaseModel):
    data_inicio: datetime
    data_fim: datetime
    igreja_id: Optional[int] = None
    membro_id: Optional[int] = None
    departamento_id: Optional[int] = None
    ministerio_id: Optional[int] = None
    tipo_evento_id: Optional[int] = None
    incluir_cancelados: bool = False
