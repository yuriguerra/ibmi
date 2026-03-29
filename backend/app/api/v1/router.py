"""Router principal da API v1: inclui todos os contextos."""
from fastapi import APIRouter

from app.agenda_escalas.api import router as agenda_escalas_router
from app.auth.api import router as auth_router
from app.estrutura_eclesiastica.api import router as estrutura_eclesiastica_router
from app.pessoas_ministerios.api import router as pessoas_ministerios_router
from app.relatorios_historico.api import router as relatorios_historico_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(
    pessoas_ministerios_router,
    prefix="/pessoas-ministerios",
    tags=["pessoas-ministerios"],
)
api_router.include_router(
    estrutura_eclesiastica_router,
    prefix="/estrutura-eclesiastica",
    tags=["estrutura-eclesiastica"],
)
api_router.include_router(
    agenda_escalas_router,
    prefix="/agenda-escalas",
    tags=["agenda-escalas"],
)
api_router.include_router(
    relatorios_historico_router,
    prefix="/relatorios",
    tags=["relatorios"],
)


@api_router.get("/health")
async def health():
    """Health check para deploy e load balancer."""
    return {"status": "ok"}
