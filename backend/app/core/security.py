"""Utilitários de segurança: hash de senha e tokens JWT."""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
import bcrypt

from app.core.config import get_settings

settings = get_settings()

# ─── Senha ────────────────────────────────────────────────────────────────────

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


# ─── Tokens JWT ───────────────────────────────────────────────────────────────

def _create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    """Cria um token JWT com tempo de expiração."""
    payload = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: int | str) -> str:
    """Cria um access token JWT de curta duração."""
    return _create_token(
        data={"sub": str(subject), "type": "access"},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(subject: int | str) -> str:
    """Cria um refresh token JWT de longa duração."""
    return _create_token(
        data={"sub": str(subject), "type": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
