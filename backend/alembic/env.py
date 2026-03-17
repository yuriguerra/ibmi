"""
Alembic env.py — configurado para:
  - engine async (asyncpg)
  - leitura do DATABASE_URL via Settings (mesmo .env da aplicação)
  - importação de todos os modelos via app.shared.all_models
  - geração automática de migrations (--autogenerate)
"""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ─── Configuração do Alembic ──────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ─── Importar Settings para obter DATABASE_URL ────────────────────────────────
# Isso garante que o Alembic usa exatamente a mesma URL que a aplicação.
from app.core.config import get_settings  # noqa: E402

settings = get_settings()

# Substituir a URL no config do Alembic (sobrescreve o valor vazio do alembic.ini)
# asyncpg → psycopg2 para operações síncronas do Alembic em modo offline
# No modo online usamos o driver async diretamente.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# ─── Importar TODOS os modelos para popular o metadata ────────────────────────
# CRÍTICO: sem este import, o --autogenerate não detecta as tabelas.
import app.shared.all_models  # noqa: F401, E402
from app.core.database import Base  # noqa: E402

target_metadata = Base.metadata


# ─── Modo offline (gera SQL sem conectar ao banco) ────────────────────────────
def run_migrations_offline() -> None:
    """Gera SQL de migration sem conexão ao banco."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Detecta remoção de tabelas/colunas no autogenerate
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ─── Modo online async ────────────────────────────────────────────────────────
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
