#!/usr/bin/env python
"""
CLI para criar o primeiro usuário ADMIN.

Uso (com venv ativo, na pasta backend/):
    python scripts/create_admin.py

Ou passando variáveis diretamente:
    ADMIN_EMAIL=admin@ibmi.app ADMIN_PASSWORD=s3nh@F0rte python scripts/create_admin.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Garante que backend/ está no PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.shared.all_models # noqa: F401 — importa todos os modelos para metadata
from app.auth.models.usuario import Usuario  # noqa: F401 — necessário para metadata
from app.core.config import get_settings
from app.core.security import get_password_hash

settings = get_settings()


async def create_admin(email: str, password: str) -> None:
    if len(password) < 8:
        print("❌ Senha deve ter ao menos 8 caracteres.")
        sys.exit(1)


    database_url = os.getenv("ALEMBIC_DATABASE_URL") or settings.DATABASE_URL
    engine = create_async_engine(database_url, echo=False)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        result = await db.execute(select(Usuario).where(Usuario.email == email))
        existing = result.scalars().first()

        if existing:
            print(f"⚠️  Usuário '{email}' já existe (perfil: {existing.perfil}).")
            await engine.dispose()
            return

        admin = Usuario(
            email=email,
            hashed_password=get_password_hash(password),
            perfil="ADMIN",
            ativo=True,
        )
        db.add(admin)
        await db.commit()
        print(f"✅ ADMIN criado com sucesso: {email}")

    await engine.dispose()


def main() -> None:
    email = os.getenv("ADMIN_EMAIL") or input("E-mail do ADMIN: ").strip()
    password = os.getenv("ADMIN_PASSWORD") or input("Senha (mín. 8 chars): ").strip()

    if not email:
        print("❌ E-mail não pode ser vazio.")
        sys.exit(1)

    asyncio.run(create_admin(email, password))


if __name__ == "__main__":
    main()
