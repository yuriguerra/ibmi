"""Serviços: CRUD de Igreja e Departamento."""
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


class IgrejaService:

    # ─── Igreja ───────────────────────────────────────────────────────────────

    async def listar(
        self,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Igreja]:
        result = await db.execute(
            select(Igreja).order_by(Igreja.nome).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def obter(self, db: AsyncSession, igreja_id: int) -> Optional[Igreja]:
        return await db.get(Igreja, igreja_id)

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
        igreja = await db.get(Igreja, igreja_id)
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
        igreja = await db.get(Igreja, igreja_id)
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
    ) -> List[Departamento]:
        result = await db.execute(
            select(Departamento)
            .where(Departamento.igreja_id == igreja_id)
            .order_by(Departamento.nome)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def obter_departamento(
        self, db: AsyncSession, departamento_id: int
    ) -> Optional[Departamento]:
        return await db.get(Departamento, departamento_id)

    async def criar_departamento(
        self,
        db: AsyncSession,
        data: DepartamentoCreate,
    ) -> Departamento:
        igreja = await db.get(Igreja, data.igreja_id)
        if not igreja:
            raise ValueError(f"Igreja {data.igreja_id} não encontrada.")
        departamento = Departamento(**data.model_dump())
        db.add(departamento)
        await db.flush()
        await db.refresh(departamento)
        return departamento

    async def atualizar_departamento(
        self,
        db: AsyncSession,
        departamento_id: int,
        data: DepartamentoUpdate,
    ) -> Optional[Departamento]:
        departamento = await db.get(Departamento, departamento_id)
        if not departamento:
            return None
        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(departamento, campo, valor)
        await db.flush()
        await db.refresh(departamento)
        return departamento

    async def deletar_departamento(
        self, db: AsyncSession, departamento_id: int
    ) -> bool:
        departamento = await db.get(Departamento, departamento_id)
        if not departamento:
            return False
        await db.delete(departamento)
        return True

    # ─── Helpers ──────────────────────────────────────────────────────────────

    async def _validar_igreja_mae(
        self,
        db: AsyncSession,
        igreja_mae_id: Optional[int],
        tipo: str,
    ) -> None:
        """
        Regras:
        - CONGREGACAO deve ter igreja_mae_id.
        - MATRIZ não deve ter igreja_mae_id.
        - igreja_mae_id deve existir e ser MATRIZ.
        """
        if tipo == "CONGREGACAO":
            if not igreja_mae_id:
                raise ValueError("CONGREGACAO deve informar igreja_mae_id.")
            mae = await db.get(Igreja, igreja_mae_id)
            if not mae:
                raise ValueError(f"Igreja mãe {igreja_mae_id} não encontrada.")
            if mae.tipo != "MATRIZ":
                raise ValueError("Igreja mãe deve ser do tipo MATRIZ.")
        elif tipo == "MATRIZ" and igreja_mae_id:
            raise ValueError("MATRIZ não deve ter igreja_mae_id.")


igreja_service = IgrejaService()
