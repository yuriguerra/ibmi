"""Serviço de autenticação: login, registro, refresh e logout."""
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models.refresh_token import RefreshToken
from app.auth.models.usuario import Usuario
from app.auth.schemas.auth import RegisterRequest, TokenResponse
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)

settings = get_settings()


def _hash_token(token: str) -> str:
    """Hash simples SHA-256 para refresh token (não bcrypt — sem custo de CPU)."""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:

    # ─── Registro ─────────────────────────────────────────────────────────────

    async def register(
        self,
        db: AsyncSession,
        data: RegisterRequest,
    ) -> Usuario:
        """
        Cria novo usuário. Restrito a ADMIN autenticado (verificado no router).

        Raises:
            ValueError: se e-mail já cadastrado ou membro_id inválido.
        """
        # Verificar e-mail duplicado
        existing = await db.execute(
            select(Usuario).where(Usuario.email == data.email)
        )
        if existing.scalars().first():
            raise ValueError("E-mail já cadastrado.")

        # Verificar membro_id se fornecido
        if data.membro_id is not None:
            from app.pessoas_ministerios.models.membro import Membro
            membro = await db.get(Membro, data.membro_id)
            if membro is None:
                raise ValueError(f"Membro {data.membro_id} não encontrado.")

        usuario = Usuario(
            email=data.email,
            hashed_password=get_password_hash(data.password),
            perfil=data.perfil,
            membro_id=data.membro_id,
            ativo=True,
        )
        db.add(usuario)
        await db.flush()
        await db.refresh(usuario)
        return usuario

    # ─── Login ────────────────────────────────────────────────────────────────

    async def login(
        self,
        db: AsyncSession,
        email: str,
        password: str,
    ) -> TokenResponse:
        """
        Autentica usuário e emite access + refresh token.

        Upsert no RefreshToken: revoga token anterior e cria novo
        (1 sessão ativa por usuário).

        Raises:
            ValueError: credenciais inválidas ou usuário inativo.
        """
        result = await db.execute(
            select(Usuario).where(Usuario.email == email)
        )
        usuario = result.scalars().first()

        if not usuario or not verify_password(password, usuario.hashed_password):
            raise ValueError("Credenciais inválidas.")
        if not usuario.ativo:
            raise ValueError("Usuário inativo.")

        return await self._emitir_tokens(db, usuario)

    # ─── Refresh ──────────────────────────────────────────────────────────────

    async def refresh(
        self,
        db: AsyncSession,
        raw_token: str,
    ) -> TokenResponse:
        """
        Valida refresh token e emite novo par de tokens (rotação).

        Raises:
            ValueError: token inválido, revogado ou expirado.
        """
        token_hash = _hash_token(raw_token)

        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        rt = result.scalars().first()

        if rt is None or rt.revogado:
            raise ValueError("Refresh token inválido ou revogado.")

        now = datetime.now(timezone.utc)
        if rt.expires_at < now:
            raise ValueError("Refresh token expirado.")

        # Revogar token atual antes de emitir novo
        rt.revogado = True
        await db.flush()

        result2 = await db.execute(
            select(Usuario).where(Usuario.id == rt.usuario_id)
        )
        usuario = result2.scalars().first()
        if not usuario or not usuario.ativo:
            raise ValueError("Usuário inativo ou não encontrado.")

        return await self._emitir_tokens(db, usuario)

    # ─── Logout ───────────────────────────────────────────────────────────────

    async def logout(self, db: AsyncSession, usuario_id: int) -> None:
        """
        Revoga o refresh token do usuário (logout real).

        O access token continua válido até expirar (30 min).
        Complexidade de blacklist não justificada para o porte.
        """
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.usuario_id == usuario_id,
                RefreshToken.revogado.is_(False),
            )
        )
        rt = result.scalars().first()
        if rt:
            rt.revogado = True
            await db.flush()

    # ─── Helpers privados ─────────────────────────────────────────────────────

    async def _emitir_tokens(
        self,
        db: AsyncSession,
        usuario: Usuario,
    ) -> TokenResponse:
        """Gera tokens e persiste/substitui o RefreshToken no banco."""
        raw_refresh = secrets.token_urlsafe(64)
        token_hash = _hash_token(raw_refresh)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        # Upsert: busca registro existente (único por usuario_id)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.usuario_id == usuario.id)
        )
        rt = result.scalars().first()

        if rt:
            rt.token_hash = token_hash
            rt.revogado = False
            rt.expires_at = expires_at
        else:
            rt = RefreshToken(
                usuario_id=usuario.id,
                token_hash=token_hash,
                revogado=False,
                expires_at=expires_at,
            )
            db.add(rt)

        await db.flush()

        return TokenResponse(
            access_token=create_access_token(usuario.id),
            refresh_token=raw_refresh,
        )


auth_service = AuthService()
