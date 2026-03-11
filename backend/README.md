# IBMI Backend

Backend FastAPI do **sistema de agenda para igrejas** (IBMI), monólito modular organizado por **contexto de domínio**.

## Estrutura por contexto

A aplicação segue os contextos definidos em `system_definitions.md`:

```
app/
├── main.py                 # Entrada FastAPI, lifespan, CORS
├── core/                   # Infraestrutura compartilhada
│   ├── config.py           # Settings (Pydantic Settings)
│   ├── database.py         # SQLAlchemy 2.0 async, get_db
│   └── security.py         # JWT, hash de senha
├── api/
│   ├── deps.py             # Dependências (get_db, get_current_user)
│   └── v1/
│       └── router.py       # Agrega todos os routers
├── auth/                   # Contexto: Autenticação e autorização
│   ├── schemas/
│   ├── services/
│   └── api.py
├── pessoas_ministerios/    # Contexto: Pessoas & Ministérios
│   ├── models/             # Membro, Ministério, associações N:N
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   └── api.py
├── estrutura_eclesiastica/ # Contexto: Estrutura Eclesiástica
│   ├── models/             # Igreja, Departamento
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   └── api.py
├── agenda_escalas/         # Contexto: Agenda & Escalas
│   ├── models/             # TipoEvento, Evento, Recorrência, Ocorrência, Escala
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   └── api.py
└── relatorios_historico/   # Contexto: Relatórios & Histórico
    ├── schemas/
    ├── services/
    └── api.py
```

## Como rodar

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # ou .venv\Scripts\activate no Windows
pip install -r requirements.txt
cp .env.example .env        # ajustar DATABASE_URL e SECRET_KEY
uvicorn app.main:app --reload
```

API em `http://localhost:8000`, documentação em `http://localhost:8000/docs`.

## Próximos passos

1. Definir modelos SQLAlchemy por contexto e Alembic.
2. Implementar auth (login, JWT, perfis Admin/Membro).
3. Implementar CRUD por contexto (estrutura eclesiástica → pessoas & ministérios → agenda & escalas).
4. Regras de visibilidade e geração de ocorrências a partir de recorrência.
