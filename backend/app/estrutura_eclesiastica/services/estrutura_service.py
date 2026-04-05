"""Serviços: CRUD de Igreja e Departamento com soft delete."""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.estrutura_eclesiastica.models.igreja import Departamento, Igreja
from app.estrutura_eclesiastica.schemas.estrutura import (
    DepartamentoCreate,
    DepartamentoUpdate,
    IgrejaCreate,
    IgrejaUpdate,
)

_AGORA = lambda: datetime.now(timezone.utc)  # noqa: E731


class IgrejaService:

    # ─── Igreja ───────────────────────────────────────────────────────────────

    async def listar(
        self,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        incluir_deletados: bool = False,
    ) -> List[Igreja]:
        q = select(Igreja).order_by(Igreja.nome).limit(limit).offset(offset)
        if not incluir_deletados:
            q = q.where(Igreja.deleted_at.is_(None))
        result = await db.execute(q)
        return list(result.scalars().all())

    async def obter(
        self,
        db: AsyncSession,
        igreja_id: int,
        incluir_deletados: bool = False,
    ) -> Optional[Igreja]:
        igreja = await db.get(Igreja, igreja_id)
        if not igreja:
            return None
        if not incluir_deletados and igreja.deleted_at is not None:
            return None
        return igreja

    async def criar(self, db: AsyncSession, data: IgrejaCreate) -> Igreja:
        await self._validar_igreja_mae(db, data.igreja_mae_id, data.tipo)
        igreja = Igreja(**data.model_dump())
        db.add(igreja)
        await db.flush()
        await db.refresh(igreja)
        return igreja

    async def atualizar(
        self,
        db: AsyncSession,
        igreja_id: int,
        data: IgrejaUpdate,
    ) -> Optional[Igreja]:
        igreja = await self.obter(db, igreja_id)
        if not igreja:
            return None
        campos = data.model_dump(exclude_unset=True)
        tipo_novo = campos.get("tipo", igreja.tipo)
        mae_nova = campos.get("igreja_mae_id", igreja.igreja_mae_id)
        await self._validar_igreja_mae(db, mae_nova, tipo_novo)
        for campo, valor in campos.items():
            setattr(igreja, campo, valor)
        await db.flush()
        await db.refresh(igreja)
        return igreja

    async def deletar(self, db: AsyncSession, igreja_id: int) -> bool:
        """Soft delete — marca deleted_at."""
        igreja = await self.obter(db, igreja_id)
        if not igreja:
            return False
        igreja.deleted_at = _AGORA()
        await db.flush()
        return True

    async def deletar_permanente(self, db: AsyncSession, igreja_id: int) -> bool:
        """Hard delete — remove fisicamente (LGPD)."""
        igreja = await self.obter(db, igreja_id, incluir_deletados=True)
        if not igreja:
            return False
        await db.delete(igreja)
        return True

    # ─── Departamento ─────────────────────────────────────────────────────────

    async def listar_departamentos(
        self,
        db: AsyncSession,
        igreja_id: int,
        limit: int = 50,
        offset: int = 0,
        incluir_deletados: bool = False,
    ) -> List[Departamento]:
        q = (
            select(Departamento)
            .where(Departamento.igreja_id == igreja_id)
            .order_by(Departamento.nome)
            .limit(limit)
            .offset(offset)
        )
        if not incluir_deletados:
            q = q.where(Departamento.deleted_at.is_(None))
        result = await db.execute(q)
        return list(result.scalars().all())

    async def obter_departamento(
        self,
        db: AsyncSession,
        departamento_id: int,
        incluir_deletados: bool = False,
    ) -> Optional[Departamento]:
        dep = await db.get(Departamento, departamento_id)
        if not dep:
            return None
        if not incluir_deletados and dep.deleted_at is not None:
            return None
        return dep

    async def criar_departamento(
        self,
        db: AsyncSession,
        data: DepartamentoCreate,
    ) -> Departamento:
        igreja = await self.obter(db, data.igreja_id)
        if not igreja:
            raise ValueError(f"Igreja {data.igreja_id} não encontrada.")
        dep = Departamento(**data.model_dump())
        db.add(dep)
        await db.flush()
        await db.refresh(dep)
        return dep

    async def atualizar_departamento(
        self,
        db: AsyncSession,
        departamento_id: int,
        data: DepartamentoUpdate,
    ) -> Optional[Departamento]:
        dep = await self.obter_departamento(db, departamento_id)
        if not dep:
            return None
        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(dep, campo, valor)
        await db.flush()
        await db.refresh(dep)
        return dep

    async def deletar_departamento(
        self, db: AsyncSession, departamento_id: int
    ) -> bool:
        """Soft delete."""
        dep = await self.obter_departamento(db, departamento_id)
        if not dep:
            return False
        dep.deleted_at = _AGORA()
        await db.flush()
        return True

    async def deletar_departamento_permanente(
        self, db: AsyncSession, departamento_id: int
    ) -> bool:
        """Hard delete (LGPD)."""
        dep = await self.obter_departamento(db, departamento_id, incluir_deletados=True)
        if not dep:
            return False
        await db.delete(dep)
        return True

    # ─── Helpers ──────────────────────────────────────────────────────────────

    async def _validar_igreja_mae(
        self,
        db: AsyncSession,
        igreja_mae_id: Optional[int],
        tipo: str,
    ) -> None:
        if tipo == "CONGREGACAO":
            if not igreja_mae_id:
                raise ValueError("CONGREGACAO deve informar igreja_mae_id.")
            mae = await self.obter(db, igreja_mae_id)
            if not mae:
                raise ValueError(f"Igreja mãe {igreja_mae_id} não encontrada.")
            if mae.tipo != "MATRIZ":
                raise ValueError("Igreja mãe deve ser do tipo MATRIZ.")
        elif tipo == "MATRIZ" and igreja_mae_id:
            raise ValueError("MATRIZ não deve ter igreja_mae_id.")


igreja_service = IgrejaService()
