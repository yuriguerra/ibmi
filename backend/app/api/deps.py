"""Dependências compartilhadas: get_db, get_current_user, etc."""
from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

# Quando auth estiver implementado:
# from app.auth.services import auth_service
# from app.auth.schemas import UserInDB
# get_current_user, get_current_active_user, require_role


def get_db_dep() -> AsyncGenerator[AsyncSession, None]:
    """Alias para uso em Depends(get_db_dep)."""
    return get_db()
