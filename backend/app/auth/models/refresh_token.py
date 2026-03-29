"""Model RefreshToken — uma sessão ativa por usuário."""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from app.core.database import Base
from app.shared.mixins import TimestampMixin


class RefreshToken(Base, TimestampMixin):
    """
    Armazena o hash do refresh token de cada sessão ativa.

    Decisões:
    - token_hash: bcrypt do token; nunca armazenar texto puro.
    - Um registro por usuário (upsert ao fazer login).
    - revogado=True permite invalidar sem deletar (histórico de auditoria futuro).
    - expires_at: usado para limpeza periódica de tokens expirados.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    usuario_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,          # 1 sessão ativa por usuário
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(Text, nullable=False)

    revogado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )

    # Relacionamento
    usuario: Mapped["Usuario"] = relationship(  # noqa: F821
        "Usuario",
        lazy="select",
    )
