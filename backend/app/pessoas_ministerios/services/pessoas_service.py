"""Serviços: CRUD de Membro e Ministério com soft delete."""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.pessoas_ministerios.models.membro import (
    Membro,
    MembroDepartamento,
    MembroMinisterio,
    Ministerio,
)
from app.pessoas_ministerios.schemas.pessoas import (
    MembroCreate,
    MembroDepartamentoCreate,
    MembroMinisterioCreate,
    MembroUpdate,
    MinisterioCreate,
    MinisterioUpdate,
)

_AGORA = lambda: datetime.now(timezone.utc)  # noqa: E731


class MinisterioService:

    async def listar(
        self,
        db: AsyncSession,
        igreja_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Ministerio]:
        q = select(Ministerio).where(Ministerio.deleted_at.is_(None))
        if igreja_id is not None:
            q = q.where(Ministerio.igreja_id == igreja_id)
        q = q.order_by(Ministerio.nome).limit(limit).offset(offset)
        result = await db.execute(q)
        return list(result.scalars().all())

    async def obter(
        self,
        db: AsyncSession,
        ministerio_id: int,
        incluir_deletados: bool = False,
    ) -> Optional[Ministerio]:
        m = await db.get(Ministerio, ministerio_id)
        if not m:
            return None
        if not incluir_deletados and m.deleted_at is not None:
            return None
        return m

    async def criar(self, db: AsyncSession, data: MinisterioCreate) -> Ministerio:
        from app.estrutura_eclesiastica.models.igreja import Igreja
        igreja = await db.get(Igreja, data.igreja_id)
        if not igreja or igreja.deleted_at is not None:
            raise ValueError(f"Igreja {data.igreja_id} não encontrada.")
        m = Ministerio(**data.model_dump())
        db.add(m)
        await db.flush()
        await db.refresh(m)
        return m

    async def atualizar(
        self,
        db: AsyncSession,
        ministerio_id: int,
        data: MinisterioUpdate,
    ) -> Optional[Ministerio]:
        m = await self.obter(db, ministerio_id)
        if not m:
            return None
        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(m, campo, valor)
        await db.flush()
        await db.refresh(m)
        return m

    async def deletar(self, db: AsyncSession, ministerio_id: int) -> bool:
        m = await self.obter(db, ministerio_id)
        if not m:
            return False
        m.deleted_at = _AGORA()
        await db.flush()
        return True

    async def deletar_permanente(self, db: AsyncSession, ministerio_id: int) -> bool:
        m = await self.obter(db, ministerio_id, incluir_deletados=True)
        if not m:
            return False
        await db.delete(m)
        return True


class MembroService:

    async def listar(
        self,
        db: AsyncSession,
        igreja_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Membro]:
        q = select(Membro).where(Membro.deleted_at.is_(None))
        if igreja_id is not None:
            q = q.where(Membro.igreja_principal_id == igreja_id)
        if status is not None:
            q = q.where(Membro.status == status)
        q = q.order_by(Membro.nome_completo).limit(limit).offset(offset)
        result = await db.execute(q)
        return list(result.scalars().all())

    async def obter(
        self,
        db: AsyncSession,
        membro_id: int,
        incluir_deletados: bool = False,
    ) -> Optional[Membro]:
        m = await db.get(Membro, membro_id)
        if not m:
            return None
        if not incluir_deletados and m.deleted_at is not None:
            return None
        return m

    async def criar(self, db: AsyncSession, data: MembroCreate) -> Membro:
        m = Membro(**data.model_dump())
        db.add(m)
        await db.flush()
        await db.refresh(m)
        return m

    async def atualizar(
        self,
        db: AsyncSession,
        membro_id: int,
        data: MembroUpdate,
    ) -> Optional[Membro]:
        m = await self.obter(db, membro_id)
        if not m:
            return None
        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(m, campo, valor)
        await db.flush()
        await db.refresh(m)
        return m

    async def deletar(self, db: AsyncSession, membro_id: int) -> bool:
        m = await self.obter(db, membro_id)
        if not m:
            return False
        m.deleted_at = _AGORA()
        await db.flush()
        return True

    async def deletar_permanente(self, db: AsyncSession, membro_id: int) -> bool:
        m = await self.obter(db, membro_id, incluir_deletados=True)
        if not m:
            return False
        await db.delete(m)
        return True

    # ─── Associações N:N ──────────────────────────────────────────────────────

    async def adicionar_departamento(
        self,
        db: AsyncSession,
        membro_id: int,
        data: MembroDepartamentoCreate,
    ) -> None:
        from app.estrutura_eclesiastica.models.igreja import Departamento
        membro = await self.obter(db, membro_id)
        if not membro:
            raise ValueError(f"Membro {membro_id} não encontrado.")
        dep = await db.get(Departamento, data.departamento_id)
        if not dep or dep.deleted_at is not None:
            raise ValueError(f"Departamento {data.departamento_id} não encontrado.")
        existente = await db.get(
            MembroDepartamento, (membro_id, data.departamento_id)
        )
        if existente:
            raise ValueError("Membro já vinculado a este departamento.")
        db.add(MembroDepartamento(membro_id=membro_id, departamento_id=data.departamento_id))
        await db.flush()

    async def remover_departamento(
        self,
        db: AsyncSession,
        membro_id: int,
        departamento_id: int,
    ) -> bool:
        vinculo = await db.get(MembroDepartamento, (membro_id, departamento_id))
        if not vinculo:
            return False
        await db.delete(vinculo)
        await db.flush()
        return True

    async def adicionar_ministerio(
        self,
        db: AsyncSession,
        membro_id: int,
        data: MembroMinisterioCreate,
    ) -> MembroMinisterio:
        membro = await self.obter(db, membro_id)
        if not membro:
            raise ValueError(f"Membro {membro_id} não encontrado.")
        min_svc = MinisterioService()
        ministerio = await min_svc.obter(db, data.ministerio_id)
        if not ministerio:
            raise ValueError(f"Ministério {data.ministerio_id} não encontrado.")
        existente = await db.get(MembroMinisterio, (membro_id, data.ministerio_id))
        if existente:
            raise ValueError("Membro já vinculado a este ministério.")
        vinculo = MembroMinisterio(
            membro_id=membro_id,
            ministerio_id=data.ministerio_id,
            funcao=data.funcao,
            observacoes=data.observacoes,
        )
        db.add(vinculo)
        await db.flush()
        await db.refresh(vinculo)
        return vinculo

    async def remover_ministerio(
        self,
        db: AsyncSession,
        membro_id: int,
        ministerio_id: int,
    ) -> bool:
        vinculo = await db.get(MembroMinisterio, (membro_id, ministerio_id))
        if not vinculo:
            return False
        await db.delete(vinculo)
        await db.flush()
        return True


ministerio_service = MinisterioService()
membro_service = MembroService()
