"""
Alembic env.py configurado para:
- engine async (asyncpg)
- ALEMBIC_DATABASE_URL com fallback para DATABASE_URL
- importacao de todos os modelos via app.shared.all_models
- geracao automatica de migrations (--autogenerate)
"""
import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv

# Garante que backend/ esta no PYTHONPATH para importar o pacote `app`
# alembic/env.py -> parent = alembic/ -> parent.parent = backend/
sys.path.insert(0, str(Path(__file__).parent.parent))

# Le o .env antes de qualquer import da aplicacao
load_dotenv()

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# --- Configuracao do Alembic --------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Resolver URL do banco ----------------------------------------------------
# Prioridade:
#   1. ALEMBIC_DATABASE_URL  -> uso local (host=localhost, porta exposta pelo Docker)
#   2. DATABASE_URL          -> padrao da aplicacao (host=db, dentro do Docker)
#
# Para rodar o Alembic localmente sem alterar o DATABASE_URL da aplicacao,
# adicione ao .env:
#   ALEMBIC_DATABASE_URL=postgresql+asyncpg://ibmi:ibmi@localhost:5432/ibmi
from app.core.config import get_settings  # noqa: E402

settings = get_settings()

database_url = os.getenv("ALEMBIC_DATABASE_URL") or settings.DATABASE_URL
config.set_main_option("sqlalchemy.url", database_url)

# --- Importar TODOS os modelos para popular o metadata -----------------------
# CRITICO: sem este import o --autogenerate nao detecta as tabelas.
import app.shared.all_models  # noqa: F401, E402
from app.core.database import Base  # noqa: E402

target_metadata = Base.metadata


# --- Modo offline (gera SQL sem conectar ao banco) ----------------------------
def run_migrations_offline() -> None:
    """Gera SQL de migration sem conexao ao banco."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# --- Modo online async --------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Cria engine async e aplica migrations."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()