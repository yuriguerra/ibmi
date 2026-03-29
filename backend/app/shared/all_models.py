"""
Importa todos os modelos SQLAlchemy da aplicação.

Este módulo é o ponto único de importação usado pelo Alembic (env.py)
para garantir que todas as tabelas estejam registradas no metadata
do Base antes de gerar ou aplicar migrations.

Ordem importa: contextos sem FK para outros contextos vêm primeiro.
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
from app.auth.models import Usuario  # noqa: F401

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
