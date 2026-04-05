"""Schemas Pydantic: autenticação e registro de usuários."""
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


# ─── Request ──────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    perfil: str = "MEMBRO"
    membro_id: Optional[int] = None

    @field_validator("perfil")
    @classmethod
    def perfil_valido(cls, v: str) -> str:
        permitidos = {"ADMIN", "MEMBRO"}
        if v not in permitidos:
            raise ValueError(f"perfil deve ser um de: {permitidos}")
        return v

    @field_validator("password")
    @classmethod
    def senha_forte(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("senha deve ter ao menos 8 caracteres")
        return v


# ─── Response ─────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UsuarioResponse(BaseModel):
    id: int
    email: str
    perfil: str
    ativo: bool
    membro_id: Optional[int]

    model_config = {"from_attributes": True}


class RefreshRequest(BaseModel):
    refresh_token: str
