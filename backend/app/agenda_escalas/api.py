"""Rotas: tipos de evento, eventos, recorrência, ocorrências, escala por ocorrência, agenda (calendário/lista)."""
from fastapi import APIRouter

router = APIRouter()


# Tipos de evento: CRUD
# Eventos (mestre): CRUD, recorrência
# Ocorrências: listagem (calendário/lista), overrides pontuais
# Escala: CRUD por ocorrência, copiar escala
# Agenda: GET com filtros (membro, departamento, ministério, igreja, tipo) e regras de visibilidade
