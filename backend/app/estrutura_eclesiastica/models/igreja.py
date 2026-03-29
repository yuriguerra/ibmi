"""Modelos de Igreja e Departamento."""
from typing import List, Optional

from sqlalchemy import BigInteger, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.mixins import TimestampMixin


class Igreja(Base, TimestampMixin):
    """
    Igreja ou congregação dentro da organização.

    Uma Igreja pode ser MATRIZ (sem mae) ou CONGREGACAO (vinculada a uma MATRIZ).
    """

    __tablename__ = "igrejas"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    endereco: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # MATRIZ | CONGREGACAO
    tipo: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="MATRIZ",
        comment="MATRIZ | CONGREGACAO",
    )

    # Auto-referência: congregação aponta para a matriz
    igreja_mae_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("igrejas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relacionamentos
    congregacoes: Mapped[List["Igreja"]] = relationship(
        "Igreja",
        back_populates="igreja_mae",
        foreign_keys=[igreja_mae_id],
    )
    igreja_mae: Mapped[Optional["Igreja"]] = relationship(
        "Igreja",
        back_populates="congregacoes",
        remote_side="Igreja.id",
        foreign_keys=[igreja_mae_id],
    )
    departamentos: Mapped[List["Departamento"]] = relationship(
        "Departamento",
        back_populates="igreja",
        cascade="all, delete-orphan",
    )


class Departamento(Base, TimestampMixin):
    """Departamento dentro de uma Igreja (ex.: Jovens, Louvor, Infância)."""

    __tablename__ = "departamentos"

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
    igreja: Mapped["Igreja"] = relationship("Igreja", back_populates="departamentos")
