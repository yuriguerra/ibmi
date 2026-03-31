"""Schemas Pydantic para Igreja e Departamento."""
from typing import Optional

from pydantic import BaseModel


# ─── Igreja ───────────────────────────────────────────────────────────────────

class IgrejaBase(BaseModel):
    nome: str
    endereco: Optional[str] = None
    tipo: str = "MATRIZ"
    igreja_mae_id: Optional[int] = None

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_tipo

    @staticmethod
    def validate_tipo(v: str) -> str:
        permitidos = {"MATRIZ", "CONGREGACAO"}
        if v not in permitidos:
            raise ValueError(f"tipo deve ser um de: {permitidos}")
        return v


class IgrejaCreate(IgrejaBase):
    pass


class IgrejaUpdate(BaseModel):
    nome: Optional[str] = None
    endereco: Optional[str] = None
    tipo: Optional[str] = None
    igreja_mae_id: Optional[int] = None


class IgrejaResponse(IgrejaBase):
    id: int

    model_config = {"from_attributes": True}


# ─── Departamento ─────────────────────────────────────────────────────────────

class DepartamentoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    igreja_id: int


class DepartamentoCreate(DepartamentoBase):
    pass


class DepartamentoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None


class DepartamentoResponse(DepartamentoBase):
    id: int

    model_config = {"from_attributes": True}
