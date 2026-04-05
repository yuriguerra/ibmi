"""Mixins reutilizáveis para modelos SQLAlchemy."""
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP


class TimestampMixin:
    """Adiciona created_at e updated_at gerenciados automaticamente."""

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SoftDeleteMixin:
    """
    Adiciona deleted_at para soft delete.

    deleted_at IS NULL  → registro ativo
    deleted_at NOT NULL → registro deletado (soft)

    Todos os SELECTs devem filtrar WHERE deleted_at IS NULL.
    Hard delete (LGPD) deve ser feito via método separado no service.
    """

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        default=None,
    )
