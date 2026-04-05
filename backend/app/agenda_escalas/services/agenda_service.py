"""
Serviços do contexto Agenda & Escalas.

Responsabilidades:
- CRUD de TipoEvento
- CRUD de Evento mestre + associações de visibilidade
- Geração de ocorrências a partir de regras de recorrência
- Overrides pontuais por ocorrência
- CRUD de escala por ocorrência + cópia entre ocorrências
- Consulta de agenda com filtros e regras de visibilidade
"""
from __future__ import annotations

import calendar
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agenda_escalas.models.agenda import (
    EscalaMinisterioOcorrencia,
    Evento,
    EventoDepartamento,
    EventoMembro,
    EventoMinisterio,
    EventoOcorrencia,
    EventoRecorrencia,
    TipoEvento,
)
from app.agenda_escalas.schemas.agenda import (
    CopiarEscalaRequest,
    EscalaCreate,
    EscalaUpdate,
    EventoCreate,
    EventoUpdate,
    OcorrenciaOverride,
    TipoEventoCreate,
    TipoEventoUpdate,
)
from app.auth.models.usuario import Usuario

_AGORA = lambda: datetime.now(timezone.utc)  # noqa: E731

# Limite de ocorrências geradas por série para evitar explosão
_MAX_OCORRENCIAS = 500


# ─── TipoEvento ───────────────────────────────────────────────────────────────

class TipoEventoService:

    async def listar(self, db: AsyncSession, limit: int = 50, offset: int = 0) -> List[TipoEvento]:
        result = await db.execute(
            select(TipoEvento).order_by(TipoEvento.nome).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def obter(self, db: AsyncSession, tipo_id: int) -> Optional[TipoEvento]:
        return await db.get(TipoEvento, tipo_id)

    async def criar(self, db: AsyncSession, data: TipoEventoCreate) -> TipoEvento:
        tipo = TipoEvento(**data.model_dump())
        db.add(tipo)
        await db.flush()
        await db.refresh(tipo)
        return tipo

    async def atualizar(
        self, db: AsyncSession, tipo_id: int, data: TipoEventoUpdate
    ) -> Optional[TipoEvento]:
        tipo = await self.obter(db, tipo_id)
        if not tipo:
            return None
        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(tipo, campo, valor)
        await db.flush()
        await db.refresh(tipo)
        return tipo

    async def deletar(self, db: AsyncSession, tipo_id: int) -> bool:
        tipo = await self.obter(db, tipo_id)
        if not tipo:
            return False
        await db.delete(tipo)
        return True


# ─── Evento ───────────────────────────────────────────────────────────────────

class EventoService:

    async def obter(self, db: AsyncSession, evento_id: int) -> Optional[Evento]:
        result = await db.execute(
            select(Evento)
            .where(Evento.id == evento_id)
            .options(selectinload(Evento.recorrencia))
        )
        return result.scalars().first()

    async def criar(self, db: AsyncSession, data: EventoCreate) -> Evento:
        """
        Cria evento mestre, associações de visibilidade e ocorrências.

        Para eventos recorrentes, gera as ocorrências imediatamente.
        Para eventos simples, cria uma única ocorrência.
        """
        e_recorrente = data.recorrencia is not None

        evento = Evento(
            titulo=data.titulo,
            descricao=data.descricao,
            local=data.local,
            visibilidade=data.visibilidade,
            e_recorrente=e_recorrente,
            data_hora_inicio=data.data_hora_inicio,
            data_hora_fim=data.data_hora_fim,
            igreja_id=data.igreja_id,
            tipo_evento_id=data.tipo_evento_id,
        )
        db.add(evento)
        await db.flush()  # obtém evento.id

        # Associações de visibilidade
        await self._sincronizar_visibilidade(db, evento, data)

        # Regra de recorrência
        if e_recorrente and data.recorrencia:
            regra = EventoRecorrencia(
                evento_id=evento.id,
                **data.recorrencia.model_dump(),
            )
            db.add(regra)
            await db.flush()
            ocorrencias = _gerar_ocorrencias(evento, data.recorrencia.model_dump())
        else:
            # Evento simples: uma única ocorrência
            ocorrencias = [
                EventoOcorrencia(
                    evento_id=evento.id,
                    data_hora_inicio=evento.data_hora_inicio,
                    data_hora_fim=evento.data_hora_fim,
                )
            ]

        for oc in ocorrencias:
            db.add(oc)

        await db.flush()
        await db.refresh(evento)
        return evento

    async def atualizar(
        self, db: AsyncSession, evento_id: int, data: EventoUpdate
    ) -> Optional[Evento]:
        evento = await self.obter(db, evento_id)
        if not evento:
            return None

        campos_simples = {
            k: v for k, v in data.model_dump(exclude_unset=True).items()
            if k not in {"departamento_ids", "ministerio_ids", "membro_ids"}
        }
        for campo, valor in campos_simples.items():
            setattr(evento, campo, valor)

        await self._sincronizar_visibilidade(db, evento, data)
        await db.flush()
        await db.refresh(evento)
        return evento

    async def deletar(self, db: AsyncSession, evento_id: int) -> bool:
        evento = await db.get(Evento, evento_id)
        if not evento:
            return False
        await db.delete(evento)
        return True

    # ─── Helpers de visibilidade ──────────────────────────────────────────────

    async def _sincronizar_visibilidade(
        self,
        db: AsyncSession,
        evento: Evento,
        data: EventoCreate | EventoUpdate,
    ) -> None:
        """
        Substitui as associações de visibilidade do evento pelos IDs fornecidos.
        Ignora campos não enviados (exclude_unset).
        """
        campos = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else {}

        if "departamento_ids" in campos:
            await db.execute(
                delete(EventoDepartamento).where(EventoDepartamento.evento_id == evento.id)
            )
            for dep_id in (campos["departamento_ids"] or []):
                db.add(EventoDepartamento(evento_id=evento.id, departamento_id=dep_id))

        if "ministerio_ids" in campos:
            await db.execute(
                delete(EventoMinisterio).where(EventoMinisterio.evento_id == evento.id)
            )
            for min_id in (campos["ministerio_ids"] or []):
                db.add(EventoMinisterio(evento_id=evento.id, ministerio_id=min_id))

        if "membro_ids" in campos:
            await db.execute(
                delete(EventoMembro).where(EventoMembro.evento_id == evento.id)
            )
            for mem_id in (campos["membro_ids"] or []):
                db.add(EventoMembro(evento_id=evento.id, membro_id=mem_id))

        await db.flush()


# ─── Ocorrência ───────────────────────────────────────────────────────────────

class OcorrenciaService:

    async def obter(self, db: AsyncSession, ocorrencia_id: int) -> Optional[EventoOcorrencia]:
        return await db.get(EventoOcorrencia, ocorrencia_id)

    async def aplicar_override(
        self,
        db: AsyncSession,
        ocorrencia_id: int,
        data: OcorrenciaOverride,
    ) -> Optional[EventoOcorrencia]:
        """Aplica ajuste pontual (horário, cancelamento, nota) a uma ocorrência."""
        oc = await self.obter(db, ocorrencia_id)
        if not oc:
            return None
        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(oc, campo, valor)
        await db.flush()
        await db.refresh(oc)
        return oc

    async def listar_por_evento(
        self, db: AsyncSession, evento_id: int, incluir_cancelados: bool = False
    ) -> List[EventoOcorrencia]:
        q = (
            select(EventoOcorrencia)
            .where(EventoOcorrencia.evento_id == evento_id)
            .order_by(EventoOcorrencia.data_hora_inicio)
        )
        if not incluir_cancelados:
            q = q.where(EventoOcorrencia.cancelado.is_(False))
        result = await db.execute(q)
        return list(result.scalars().all())


# ─── Escala ───────────────────────────────────────────────────────────────────

class EscalaService:

    async def listar(
        self, db: AsyncSession, ocorrencia_id: int
    ) -> List[EscalaMinisterioOcorrencia]:
        result = await db.execute(
            select(EscalaMinisterioOcorrencia).where(
                EscalaMinisterioOcorrencia.evento_ocorrencia_id == ocorrencia_id
            )
        )
        return list(result.scalars().all())

    async def obter(
        self, db: AsyncSession, escala_id: int
    ) -> Optional[EscalaMinisterioOcorrencia]:
        return await db.get(EscalaMinisterioOcorrencia, escala_id)

    async def criar(
        self,
        db: AsyncSession,
        ocorrencia_id: int,
        data: EscalaCreate,
    ) -> EscalaMinisterioOcorrencia:
        escala = EscalaMinisterioOcorrencia(
            evento_ocorrencia_id=ocorrencia_id,
            **data.model_dump(),
        )
        db.add(escala)
        await db.flush()
        await db.refresh(escala)
        return escala

    async def atualizar(
        self,
        db: AsyncSession,
        escala_id: int,
        data: EscalaUpdate,
    ) -> Optional[EscalaMinisterioOcorrencia]:
        escala = await self.obter(db, escala_id)
        if not escala:
            return None
        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(escala, campo, valor)
        await db.flush()
        await db.refresh(escala)
        return escala

    async def deletar(self, db: AsyncSession, escala_id: int) -> bool:
        escala = await self.obter(db, escala_id)
        if not escala:
            return False
        await db.delete(escala)
        return True

    async def copiar(
        self, db: AsyncSession, data: CopiarEscalaRequest
    ) -> int:
        """
        Copia todos os itens de escala da ocorrência origem para as ocorrências destino.

        Itens já existentes (mesma ocorrência + ministério + membro) são ignorados.
        Retorna o total de itens copiados.
        """
        result = await db.execute(
            select(EscalaMinisterioOcorrencia).where(
                EscalaMinisterioOcorrencia.evento_ocorrencia_id == data.ocorrencia_origem_id
            )
        )
        itens_origem = list(result.scalars().all())
        if not itens_origem:
            return 0

        copiados = 0
        for destino_id in data.ocorrencia_destino_ids:
            for item in itens_origem:
                # Verificar duplicata
                existente = await db.execute(
                    select(EscalaMinisterioOcorrencia).where(
                        EscalaMinisterioOcorrencia.evento_ocorrencia_id == destino_id,
                        EscalaMinisterioOcorrencia.ministerio_id == item.ministerio_id,
                        EscalaMinisterioOcorrencia.membro_id == item.membro_id,
                    )
                )
                if existente.scalars().first():
                    continue
                db.add(EscalaMinisterioOcorrencia(
                    evento_ocorrencia_id=destino_id,
                    ministerio_id=item.ministerio_id,
                    membro_id=item.membro_id,
                    papel=item.papel,
                    status="PENDENTE",  # reset status na cópia
                    observacoes=item.observacoes,
                ))
                copiados += 1

        await db.flush()
        return copiados


# ─── Agenda (consulta com filtros + visibilidade) ─────────────────────────────

class AgendaService:

    async def consultar(
        self,
        db: AsyncSession,
        usuario: Usuario,
        data_inicio: datetime,
        data_fim: datetime,
        igreja_id: Optional[int] = None,
        membro_id: Optional[int] = None,
        departamento_id: Optional[int] = None,
        ministerio_id: Optional[int] = None,
        tipo_evento_id: Optional[int] = None,
        incluir_cancelados: bool = False,
    ) -> List[EventoOcorrencia]:
        """
        Retorna ocorrências no intervalo, respeitando:
        - Filtros de data, igreja, tipo, departamento, ministério, membro
        - Regras de visibilidade por perfil (ADMIN vê tudo; MEMBRO vê conforme regras)
        - Filtro por membro escalado (membro_id)
        """
        q = (
            select(EventoOcorrencia)
            .join(Evento, EventoOcorrencia.evento_id == Evento.id)
            .where(
                EventoOcorrencia.data_hora_inicio >= data_inicio,
                EventoOcorrencia.data_hora_inicio <= data_fim,
            )
            .order_by(EventoOcorrencia.data_hora_inicio)
        )

        if not incluir_cancelados:
            q = q.where(EventoOcorrencia.cancelado.is_(False))

        # Filtros básicos
        if igreja_id:
            q = q.where(Evento.igreja_id == igreja_id)
        if tipo_evento_id:
            q = q.where(Evento.tipo_evento_id == tipo_evento_id)

        # Filtro por departamento (membro pertence ao departamento do evento)
        if departamento_id:
            q = q.join(
                EventoDepartamento,
                and_(
                    EventoDepartamento.evento_id == Evento.id,
                    EventoDepartamento.departamento_id == departamento_id,
                ),
            )

        # Filtro por ministério (membro pertence ao ministério do evento)
        if ministerio_id:
            q = q.join(
                EventoMinisterio,
                and_(
                    EventoMinisterio.evento_id == Evento.id,
                    EventoMinisterio.ministerio_id == ministerio_id,
                ),
            )

        # Filtro por membro escalado
        if membro_id:
            q = q.join(
                EscalaMinisterioOcorrencia,
                and_(
                    EscalaMinisterioOcorrencia.evento_ocorrencia_id == EventoOcorrencia.id,
                    EscalaMinisterioOcorrencia.membro_id == membro_id,
                ),
            )

        # ── Visibilidade ──────────────────────────────────────────────────────
        if usuario.perfil != "ADMIN":
            q = await self._aplicar_visibilidade(db, q, usuario)

        result = await db.execute(q)
        return list(result.scalars().unique().all())

    async def _aplicar_visibilidade(self, db: AsyncSession, q, usuario: Usuario):
        """
        Filtra eventos visíveis para o usuário com perfil MEMBRO.

        Visível quando:
          1. evento.visibilidade = GERAL
          2. POR_DEPARTAMENTO e usuário está em um dos departamentos
          3. POR_MINISTERIO e usuário está em um dos ministérios
          4. POR_MEMBRO e usuário está na lista de membros explícitos
        """
        membro_id = usuario.membro_id
        if membro_id is None:
            # Sem vínculo com membro: só vê eventos GERAL
            return q.where(Evento.visibilidade == "GERAL")

        # Busca departamentos e ministérios do membro
        from app.pessoas_ministerios.models.membro import MembroDepartamento, MembroMinisterio

        dep_result = await db.execute(
            select(MembroDepartamento.departamento_id).where(
                MembroDepartamento.membro_id == membro_id
            )
        )
        dep_ids = [r for r, in dep_result.all()]

        min_result = await db.execute(
            select(MembroMinisterio.ministerio_id).where(
                MembroMinisterio.membro_id == membro_id
            )
        )
        min_ids = [r for r, in min_result.all()]

        condicoes = [Evento.visibilidade == "GERAL"]

        if dep_ids:
            condicoes.append(
                and_(
                    Evento.visibilidade == "POR_DEPARTAMENTO",
                    Evento.id.in_(
                        select(EventoDepartamento.evento_id).where(
                            EventoDepartamento.departamento_id.in_(dep_ids)
                        )
                    ),
                )
            )

        if min_ids:
            condicoes.append(
                and_(
                    Evento.visibilidade == "POR_MINISTERIO",
                    Evento.id.in_(
                        select(EventoMinisterio.evento_id).where(
                            EventoMinisterio.ministerio_id.in_(min_ids)
                        )
                    ),
                )
            )

        condicoes.append(
            and_(
                Evento.visibilidade == "POR_MEMBRO",
                Evento.id.in_(
                    select(EventoMembro.evento_id).where(
                        EventoMembro.membro_id == membro_id
                    )
                ),
            )
        )

        return q.where(or_(*condicoes))


# ─── Geração de ocorrências ───────────────────────────────────────────────────

def _gerar_ocorrencias(evento: Evento, regra: dict) -> List[EventoOcorrencia]:
    """
    Gera lista de EventoOcorrencia a partir da regra de recorrência.

    Suporte a:
    - DAILY com intervalo
    - WEEKLY com dias_semana e intervalo (ex.: sexta a cada 2 semanas)
    - MONTHLY com dias_mes (ex.: todo dia 15) OU posicao_na_semana + dia_semana_posicao
      (ex.: primeiro domingo = posicao=1, dia_semana=0)

    Fim da série: data_fim OU ocorrencias_max (o que vier primeiro).
    """
    frequencia: str = regra["frequencia"]
    intervalo: int = regra.get("intervalo") or 1
    dias_semana: list = regra.get("dias_semana") or []
    dias_mes: list = regra.get("dias_mes") or []
    posicao_na_semana: Optional[int] = regra.get("posicao_na_semana")
    dia_semana_posicao: Optional[int] = regra.get("dia_semana_posicao")
    data_fim: Optional[datetime] = regra.get("data_fim")
    ocorrencias_max: Optional[int] = regra.get("ocorrencias_max")

    duracao = evento.data_hora_fim - evento.data_hora_inicio
    inicio = evento.data_hora_inicio
    ocorrencias: List[EventoOcorrencia] = []

    def _adicionar(dt: datetime) -> bool:
        """Adiciona ocorrência se dentro dos limites. Retorna False quando encerrar."""
        if data_fim and dt > data_fim:
            return False
        if ocorrencias_max and len(ocorrencias) >= ocorrencias_max:
            return False
        if len(ocorrencias) >= _MAX_OCORRENCIAS:
            return False
        ocorrencias.append(
            EventoOcorrencia(
                evento_id=evento.id,
                data_hora_inicio=dt,
                data_hora_fim=dt + duracao,
            )
        )
        return True

    if frequencia == "DAILY":
        dt = inicio
        while True:
            if not _adicionar(dt):
                break
            dt += timedelta(days=intervalo)

    elif frequencia == "WEEKLY":
        # dias_semana: 0=Dom, 1=Seg, ..., 6=Sáb
        # Python weekday(): 0=Seg, ..., 6=Dom → converter
        _py_weekday = {0: 6, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}
        alvos = sorted(set(dias_semana)) if dias_semana else [inicio.weekday()]
        # Começa na semana do evento
        semana_inicio = inicio - timedelta(days=inicio.weekday())  # segunda da semana
        semana = semana_inicio
        parar = False
        while not parar:
            for dia_idx in alvos:
                py_wd = _py_weekday.get(dia_idx, dia_idx)
                dt = semana + timedelta(days=py_wd)
                dt = dt.replace(
                    hour=inicio.hour,
                    minute=inicio.minute,
                    second=inicio.second,
                    tzinfo=inicio.tzinfo,
                )
                if dt < inicio:
                    continue
                if not _adicionar(dt):
                    parar = True
                    break
            semana += timedelta(weeks=intervalo)

    elif frequencia == "MONTHLY":
        dt = inicio
        while True:
            if posicao_na_semana is not None and dia_semana_posicao is not None:
                # Ex.: primeiro domingo = posicao=1, dia_semana_posicao=0
                candidato = _data_posicao_semana(dt.year, dt.month, posicao_na_semana, dia_semana_posicao)
                if candidato:
                    candidato = candidato.replace(
                        hour=inicio.hour,
                        minute=inicio.minute,
                        second=inicio.second,
                        tzinfo=inicio.tzinfo,
                    )
                    if candidato >= inicio:
                        if not _adicionar(candidato):
                            break
            elif dias_mes:
                for dia in sorted(set(dias_mes)):
                    try:
                        candidato = dt.replace(day=dia)
                    except ValueError:
                        continue  # dia inválido para o mês (ex.: 31 em fevereiro)
                    candidato = candidato.replace(
                        hour=inicio.hour,
                        minute=inicio.minute,
                        second=inicio.second,
                        tzinfo=inicio.tzinfo,
                    )
                    if candidato < inicio:
                        continue
                    if not _adicionar(candidato):
                        break
            else:
                # Fallback: mesmo dia do mês
                try:
                    candidato = dt.replace(day=inicio.day)
                    if candidato >= inicio:
                        if not _adicionar(candidato):
                            break
                except ValueError:
                    pass

            # Avança pelo número de meses do intervalo
            mes = dt.month - 1 + intervalo
            ano = dt.year + mes // 12
            mes = mes % 12 + 1
            dt = dt.replace(year=ano, month=mes, day=1)

            # Verificar limite geral
            if data_fim and dt > data_fim:
                break
            if ocorrencias_max and len(ocorrencias) >= ocorrencias_max:
                break
            if len(ocorrencias) >= _MAX_OCORRENCIAS:
                break

    return ocorrencias


def _data_posicao_semana(
    ano: int, mes: int, posicao: int, dia_semana: int
) -> Optional[datetime]:
    """
    Retorna a data do N-ésimo dia_semana no mês.

    dia_semana: 0=Dom, 1=Seg, ..., 6=Sáb
    posicao: 1=primeiro, 2=segundo, ..., -1=último

    Exemplo: posicao=1, dia_semana=0 → primeiro domingo do mês
    """
    # Converter para python weekday (0=Seg…6=Dom)
    _py = {0: 6, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}
    py_wd = _py.get(dia_semana, dia_semana)

    _, dias_no_mes = calendar.monthrange(ano, mes)
    dias = [
        datetime(ano, mes, d)
        for d in range(1, dias_no_mes + 1)
        if datetime(ano, mes, d).weekday() == py_wd
    ]
    if not dias:
        return None

    try:
        return dias[posicao - 1] if posicao > 0 else dias[posicao]
    except IndexError:
        return None


# ─── Instâncias ───────────────────────────────────────────────────────────────

tipo_evento_service = TipoEventoService()
evento_service = EventoService()
ocorrencia_service = OcorrenciaService()
escala_service = EscalaService()
agenda_service = AgendaService()
