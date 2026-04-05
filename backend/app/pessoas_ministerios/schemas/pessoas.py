"""Schemas Pydantic para Membro, Ministério e associações N:N."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr


# ─── Ministério ───────────────────────────────────────────────────────────────

class MinisterioBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    igreja_id: int


class MinisterioCreate(MinisterioBase):
    pass


class MinisterioUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None


class MinisterioResponse(MinisterioBase):
    id: int

    model_config = {"from_attributes": True}


# ─── Membro ───────────────────────────────────────────────────────────────────

class MembroBase(BaseModel):
    nome_completo: str
    data_nascimento: Optional[date] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    status: str = "ATIVO"
    igreja_principal_id: Optional[int] = None


class MembroCreate(MembroBase):
    pass


class MembroUpdate(BaseModel):
    nome_completo: Optional[str] = None
    data_nascimento: Optional[date] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    status: Optional[str] = None
    igreja_principal_id: Optional[int] = None


class MembroResponse(MembroBase):
    id: int

    model_config = {"from_attributes": True}


# ─── Associações N:N ──────────────────────────────────────────────────────────

class MembroDepartamentoCreate(BaseModel):
    departamento_id: int


class MembroMinisterioCreate(BaseModel):
    ministerio_id: int
    funcao: Optional[str] = None
    observacoes: Optional[str] = None


class MembroMinisterioResponse(BaseModel):
    ministerio_id: int
    funcao: Optional[str] = None
    observacoes: Optional[str] = None

    model_config = {"from_attributes": True}
