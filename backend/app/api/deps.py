"""Dependências compartilhadas: autenticação e autorização por perfil."""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models.usuario import Usuario
from app.core.config import get_settings
from app.core.database import get_db

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciais inválidas ou token expirado.",
    headers={"WWW-Authenticate": "Bearer"},
)
_403 = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Acesso restrito a administradores.",
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Usuario:
    """
    Decodifica o JWT e retorna o usuário autenticado.

    Raises 401 se o token for inválido, expirado ou o usuário não existir/inativo.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        tipo: str | None = payload.get("type")
        sub: str | None = payload.get("sub")

        if tipo != "access" or sub is None:
            raise _401
    except JWTError:
        raise _401

    usuario = await db.get(Usuario, int(sub))
    if usuario is None or not usuario.ativo:
        raise _401

    return usuario


async def require_admin(
    current_user: Annotated[Usuario, Depends(get_current_user)],
) -> Usuario:
    """
    Garante que o usuário autenticado é ADMIN.

    Raises 403 caso contrário.
    """
    if current_user.perfil != "ADMIN":
        raise _403
    return current_user


# Aliases tipados para uso com Annotated nos routers
CurrentUser = Annotated[Usuario, Depends(get_current_user)]
AdminUser = Annotated[Usuario, Depends(require_admin)]
