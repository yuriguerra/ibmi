"""Rotas do contexto Estrutura Eclesiástica: igrejas, congregações, departamentos."""
from fastapi import APIRouter

router = APIRouter()


# Igrejas: CRUD, listagem (matriz/congregação, igreja_mae_id)
# Departamentos: CRUD por igreja_id
