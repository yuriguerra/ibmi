"""
Modelos do contexto Agenda & Escalas.

Hierarquia:
  Evento (mestre) → EventoRecorrencia (regra) → EventoOcorrencia (instância concreta)
  EventoOcorrencia → EscalaMinisterioOcorrencia (quem serve em qual dia)

Visibilidade:
  Evento.visibilidade = GERAL | POR_DEPARTAMENTO | POR_MINISTERIO | POR_MEMBRO
  Tabelas de associação determinam quem vê eventos restritos.
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import ARRAY, TIMESTAMP

from app.core.database import Base
from app.shared.mixins import TimestampMixin


# ─── Tipo de Evento ───────────────────────────────────────────────────────────

class TipoEvento(Base, TimestampMixin):
    """Classifica eventos: Culto, Ensaio, Reunião, Congresso, etc."""

    __tablename__ = "tipos_evento"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cor: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Hex color, ex: #FF5733")


# ─── Visibilidade (tabelas de associação) ─────────────────────────────────────

class EventoDepartamento(Base):
    """Restringe visibilidade de um Evento a Departamentos específicos."""

    __tablename__ = "evento_departamento"

    evento_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("eventos.id", ondelete="CASCADE"), primary_key=True
    )
    departamento_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("departamentos.id", ondelete="CASCADE"), primary_key=True
    )


class EventoMinisterio(Base):
    """Restringe visibilidade de um Evento a Ministérios específicos."""

    __tablename__ = "evento_ministerio"

    evento_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("eventos.id", ondelete="CASCADE"), primary_key=True
    )
    ministerio_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ministerios.id", ondelete="CASCADE"), primary_key=True
    )


class EventoMembro(Base):
    """Restringe visibilidade de um Evento a Membros específicos."""

    __tablename__ = "evento_membro"

    evento_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("eventos.id", ondelete="CASCADE"), primary_key=True
    )
    membro_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("membros.id", ondelete="CASCADE"), primary_key=True
    )


# ─── Evento Mestre ────────────────────────────────────────────────────────────

class Evento(Base, TimestampMixin):
    """
    Template/mestre de um evento.

    Para eventos não-recorrentes, é o evento em si.
    Para recorrentes, gera EventoOcorrencia via EventoRecorrencia.
    """

    __tablename__ = "eventos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    local: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # GERAL | POR_DEPARTAMENTO | POR_MINISTERIO | POR_MEMBRO
    visibilidade: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="GERAL",
        comment="GERAL | POR_DEPARTAMENTO | POR_MINISTERIO | POR_MEMBRO",
    )

    e_recorrente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    data_hora_inicio: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    data_hora_fim: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )

    igreja_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("igrejas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo_evento_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("tipos_evento.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relacionamentos
    igreja: Mapped["Igreja"] = relationship("Igreja", lazy="select")  # noqa: F821
    tipo_evento: Mapped[Optional["TipoEvento"]] = relationship("TipoEvento", lazy="select")
    recorrencia: Mapped[Optional["EventoRecorrencia"]] = relationship(
        "EventoRecorrencia", back_populates="evento", uselist=False, cascade="all, delete-orphan"
    )
    ocorrencias: Mapped[List["EventoOcorrencia"]] = relationship(
        "EventoOcorrencia", back_populates="evento", cascade="all, delete-orphan"
    )
    departamentos_visibilidade: Mapped[List["EventoDepartamento"]] = relationship(
        "EventoDepartamento", cascade="all, delete-orphan"
    )
    ministerios_visibilidade: Mapped[List["EventoMinisterio"]] = relationship(
        "EventoMinisterio", cascade="all, delete-orphan"
    )
    membros_visibilidade: Mapped[List["EventoMembro"]] = relationship(
        "EventoMembro", cascade="all, delete-orphan"
    )


# ─── Regra de Recorrência ─────────────────────────────────────────────────────

class EventoRecorrencia(Base):
    """
    Define a regra de recorrência de um Evento mestre.

    frequencia: DAILY | WEEKLY | MONTHLY
    intervalo:  1 = toda semana; 2 = a cada 2 semanas
    dias_semana: lista de dias (0=Dom … 6=Sáb), ex: [5] = toda sexta
    dias_mes:   lista de dias do mês, ex: [15] = todo dia 15
    posicao_na_semana: 1 = primeiro, 2 = segundo, -1 = último
    dia_semana_posicao: 0-6, usado junto com posicao_na_semana

    Fim da série: data_fim OU ocorrencias_max (o que vier primeiro).
    """

    __tablename__ = "evento_recorrencia"

    evento_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("eventos.id", ondelete="CASCADE"), primary_key=True
    )

    # DAILY | WEEKLY | MONTHLY
    frequencia: Mapped[str] = mapped_column(Text, nullable=False, comment="DAILY | WEEKLY | MONTHLY")
    intervalo: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Armazenados como arrays de inteiros no PostgreSQL
    dias_semana: Mapped[Optional[List[int]]] = mapped_column(
        ARRAY(Integer), nullable=True, comment="0=Dom,1=Seg,...,6=Sab"
    )
    dias_mes: Mapped[Optional[List[int]]] = mapped_column(
        ARRAY(Integer), nullable=True, comment="1-31"
    )

    # Para "primeiro domingo do mês": posicao_na_semana=1, dia_semana_posicao=0
    posicao_na_semana: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="1=primeiro, 2=segundo, -1=último"
    )
    dia_semana_posicao: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="0=Dom,...,6=Sab — usado com posicao_na_semana"
    )

    data_fim: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    ocorrencias_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relacionamento
    evento: Mapped["Evento"] = relationship("Evento", back_populates="recorrencia")


# ─── Ocorrência Concreta ──────────────────────────────────────────────────────

class EventoOcorrencia(Base):
    """
    Instância concreta de um Evento no calendário.

    Gerada a partir da regra de recorrência (ou única para eventos não-recorrentes).
    Permite overrides pontuais: cancelamento, horário diferente, nota.
    Base de todas as queries de agenda.
    """

    __tablename__ = "evento_ocorrencia"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    evento_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("eventos.id", ondelete="CASCADE"), nullable=False, index=True
    )

    data_hora_inicio: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    data_hora_fim: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    # Override: cancelada individualmente?
    cancelado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Override: nota específica desta ocorrência
    nota_ocorrencia: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relacionamentos
    evento: Mapped["Evento"] = relationship("Evento", back_populates="ocorrencias")
    escala: Mapped[List["EscalaMinisterioOcorrencia"]] = relationship(
        "EscalaMinisterioOcorrencia", back_populates="ocorrencia", cascade="all, delete-orphan"
    )


# ─── Escala de Ministério por Ocorrência ──────────────────────────────────────

class EscalaMinisterioOcorrencia(Base, TimestampMixin):
    """
    Define quem serve em qual ministério em uma ocorrência específica.

    status: PENDENTE | CONFIRMADO | CANCELADO | SUBSTITUTO
    """

    __tablename__ = "escala_ministerio_ocorrencia"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    evento_ocorrencia_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("evento_ocorrencia.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ministerio_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("ministerios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    membro_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("membros.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    papel: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Ex: líder de louvor, músico, intercessor"
    )

    # PENDENTE | CONFIRMADO | CANCELADO | SUBSTITUTO
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="PENDENTE",
        comment="PENDENTE | CONFIRMADO | CANCELADO | SUBSTITUTO",
    )

    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relacionamentos
    ocorrencia: Mapped["EventoOcorrencia"] = relationship(
        "EventoOcorrencia", back_populates="escala"
    )
    ministerio: Mapped["Ministerio"] = relationship("Ministerio", lazy="select")  # noqa: F821
    membro: Mapped["Membro"] = relationship("Membro", lazy="select")  # noqa: F821
