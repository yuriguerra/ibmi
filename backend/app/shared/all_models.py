"""
Importa todos os modelos SQLAlchemy da aplicação.

Ponto único usado pelo Alembic para registrar todas as tabelas no metadata.
Ordem: sem FKs externas → com FKs → dependentes.
"""

# 1. Estrutura eclesiástica (sem FKs externas)
from app.estrutura_eclesiastica.models import Departamento, Igreja  # noqa: F401

# 2. Pessoas & Ministérios (FK → Igreja, Departamento)
from app.pessoas_ministerios.models import (  # noqa: F401
    Membro,
    MembroDepartamento,
    MembroMinisterio,
    Ministerio,
)

# 3. Auth (FK opcional → Membro)
from app.auth.models import RefreshToken, Usuario  # noqa: F401

# 4. Agenda & Escalas (FK → Igreja, TipoEvento, Membro, Ministério, Departamento)
from app.agenda_escalas.models import (  # noqa: F401
    EscalaMinisterioOcorrencia,
    Evento,
    EventoDepartamento,
    EventoMembro,
    EventoMinisterio,
    EventoOcorrencia,
    EventoRecorrencia,
    TipoEvento,
)
