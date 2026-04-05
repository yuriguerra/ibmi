"""add_soft_delete

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-03-31 00:00:00.000000

Adiciona coluna deleted_at (TIMESTAMPTZ, nullable) nas entidades
que suportam soft delete: igrejas, departamentos, membros,
ministerios, usuarios.

deleted_at IS NULL     → registro ativo
deleted_at IS NOT NULL → registro soft-deletado
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELAS = [
    "igrejas",
    "departamentos",
    "membros",
    "ministerios",
    "usuarios",
]


def upgrade() -> None:
    for tabela in TABELAS:
        op.add_column(
            tabela,
            sa.Column(
                "deleted_at",
                sa.TIMESTAMP(timezone=True),
                nullable=True,
                server_default=None,
            ),
        )
        # Índice parcial: acelera queries de registros ativos (WHERE deleted_at IS NULL)
        op.create_index(
            f"ix_{tabela}_deleted_at",
            tabela,
            ["deleted_at"],
            postgresql_where=sa.text("deleted_at IS NULL"),
        )


def downgrade() -> None:
    for tabela in reversed(TABELAS):
        op.drop_index(f"ix_{tabela}_deleted_at", table_name=tabela)
        op.drop_column(tabela, "deleted_at")
