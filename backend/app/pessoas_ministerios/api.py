"""Rotas do contexto Pessoas & Ministérios: membros, ministérios, vínculos."""
from fastapi import APIRouter

router = APIRouter()


# Membros: CRUD, listagem por igreja/departamento/ministério
# Ministérios: CRUD por igreja
# Associações: membro-departamento (N:N), membro-ministério (N:N + função)
