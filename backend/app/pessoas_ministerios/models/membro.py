"""Modelos de Membro, Ministério e suas associações N:N."""
from datetime import date
from typing import List, Optional

from sqlalchemy import BigInteger, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.mixins import TimestampMixin


# ─── Tabelas de associação N:N ────────────────────────────────────────────────

class MembroDepartamento(Base):
    """Associação N:N entre Membro e Departamento."""

    __tablename__ = "membro_departamento"

    membro_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("membros.id", ondelete="CASCADE"),
        primary_key=True,
    )
    departamento_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("departamentos.id", ondelete="CASCADE"),
        primary_key=True,
    )


class MembroMinisterio(Base):
    """Associação N:N entre Membro e Ministério, com função opcional."""

    __tablename__ = "membro_ministerio"

    membro_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("membros.id", ondelete="CASCADE"),
        primary_key=True,
    )
    ministerio_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("ministerios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    funcao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ─── Entidades principais ─────────────────────────────────────────────────────

class Membro(Base, TimestampMixin):
    """
    Pessoa cadastrada na organização.

    Pode ou não ter um Usuario vinculado para acesso ao sistema.
    Status controla participação ativa: ATIVO | EM_OBSERVACAO | DESLIGADO.
    """

    __tablename__ = "membros"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome_completo: Mapped[str] = mapped_column(Text, nullable=False)
    data_nascimento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    telefone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ATIVO | EM_OBSERVACAO | DESLIGADO
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="ATIVO",
        comment="ATIVO | EM_OBSERVACAO | DESLIGADO",
    )

    igreja_principal_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("igrejas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relacionamentos
    igreja_principal: Mapped[Optional["Igreja"]] = relationship(  # noqa: F821
        "Igreja",
        lazy="select",
    )
    departamentos: Mapped[List["Departamento"]] = relationship(  # noqa: F821
        "Departamento",
        secondary="membro_departamento",
        lazy="select",
    )
    ministerios: Mapped[List["Ministerio"]] = relationship(
        "Ministerio",
        secondary="membro_ministerio",
        lazy="select",
    )
    # Vínculo inverso com Usuario (um Membro pode ter um Usuário)
    usuario: Mapped[Optional["Usuario"]] = relationship(  # noqa: F821
        "Usuario",
        back_populates="membro",
        lazy="select",
    )


class Ministerio(Base, TimestampMixin):
    """
    Ministério dentro de uma Igreja (ex.: Louvor, Intercessão, Recepção).

    Usado principalmente para construção de escalas de serviço.
    """

    __tablename__ = "ministerios"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    igreja_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("igrejas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relacionamentos
    igreja: Mapped["Igreja"] = relationship("Igreja", lazy="select")  # noqa: F821
