"""Modelo de Usuário — credenciais e perfil de acesso."""
from typing import Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.mixins import SoftDeleteMixin, TimestampMixin


class Usuario(Base, TimestampMixin, SoftDeleteMixin):
    """
    Representa um usuário do sistema (credenciais + perfil).

    Separado de Membro deliberadamente:
    - Um Admin pode existir sem ser membro de nenhuma igreja.
    - Um Membro pode existir no cadastro sem ter acesso ao sistema.
    - A vinculação é opcional via membro_id.

    Soft delete padrão. Hard delete disponível para atender LGPD.
    """

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)

    perfil: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="MEMBRO",
        comment="ADMIN | MEMBRO",
    )

    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    membro_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("membros.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    membro: Mapped[Optional["Membro"]] = relationship(  # noqa: F821
        "Membro",
        back_populates="usuario",
        lazy="select",
    )
