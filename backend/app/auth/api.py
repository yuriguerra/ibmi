"""Rotas de autenticação: login, refresh, logout, registro (ADMIN) e /me."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser, CurrentUser
from app.auth.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UsuarioResponse,
)
from app.auth.services.auth_service import auth_service
from app.core.database import get_db

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autenticar usuário",
    description="Retorna access token (JWT, 30 min) e refresh token (opaco, 7 dias).",
)
async def login(
    data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    try:
        return await auth_service.login(db, data.email, data.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar tokens",
    description="Valida refresh token e emite novo par. O token anterior é revogado (rotação).",
)
async def refresh(
    data: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    try:
        return await auth_service.refresh(db, data.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Encerrar sessão",
    description="Revoga o refresh token. O access token expira naturalmente (30 min).",
)
async def logout(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await auth_service.logout(db, current_user.id)


@router.post(
    "/register",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuário (ADMIN)",
    description="Cria novo usuário. Restrito a administradores autenticados.",
)
async def register(
    data: RegisterRequest,
    _admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UsuarioResponse:
    try:
        usuario = await auth_service.register(db, data)
        return UsuarioResponse.model_validate(usuario)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Usuário atual",
    description="Retorna os dados do usuário autenticado.",
)
async def me(current_user: CurrentUser) -> UsuarioResponse:
    return UsuarioResponse.model_validate(current_user)
