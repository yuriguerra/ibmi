# IBMI Backend

Backend FastAPI do **sistema de agenda para igrejas** (IBMI), monólito modular organizado por **contexto de domínio**.

---

## Estrutura do projeto

```
backend/
├── .env.example                        # Template de variáveis de ambiente
├── .env                                # Variáveis locais (não versionar)
├── Dockerfile                          # Imagem do backend
├── docker-compose.yml                  # Postgres + Backend
├── requirements.txt                    # Dependências Python
├── alembic.ini                         # Configuração do Alembic
├── alembic/
│   ├── env.py                          # Engine async + resolução de DATABASE_URL
│   ├── script.py.mako                  # Template para arquivos de migration
│   └── versions/                       # Migrations geradas
│       ├── 20260317_221334_initial_schema.py
│       └── 20260329_000000_add_refresh_tokens.py
├── scripts/
│   └── create_admin.py                 # CLI para criar primeiro usuário ADMIN
└── app/
    ├── main.py                         # Entrada FastAPI, lifespan, CORS
    ├── shared/
    │   ├── mixins.py                   # TimestampMixin (created_at, updated_at)
    │   └── all_models.py               # Importa todos os models (usado pelo Alembic)
    ├── core/
    │   ├── config.py                   # Settings via Pydantic Settings
    │   ├── database.py                 # SQLAlchemy 2.0 async, get_db
    │   └── security.py                 # JWT, hash de senha (bcrypt direto, sem passlib)
    ├── api/
    │   ├── deps.py                     # get_current_user, require_admin, CurrentUser, AdminUser
    │   └── v1/
    │       └── router.py               # Agrega todos os routers
    ├── auth/                           # Contexto: Autenticação
    │   ├── models/
    │   │   ├── usuario.py              # Model: Usuario (credenciais + perfil)
    │   │   └── refresh_token.py        # Model: RefreshToken (1 sessão por usuário)
    │   ├── schemas/
    │   │   └── auth.py                 # LoginRequest, RegisterRequest, TokenResponse, etc.
    │   ├── services/
    │   │   └── auth_service.py         # login, register, refresh, logout
    │   └── api.py                      # POST /login, /refresh, /logout, /register; GET /me
    ├── estrutura_eclesiastica/         # Contexto: Estrutura Eclesiástica
    │   ├── models/
    │   │   └── igreja.py              # Models: Igreja, Departamento
    │   ├── schemas/
    │   ├── repositories/
    │   ├── services/
    │   └── api.py
    ├── pessoas_ministerios/            # Contexto: Pessoas & Ministérios
    │   ├── models/
    │   │   └── membro.py              # Models: Membro, Ministerio, MembroDepartamento, MembroMinisterio
    │   ├── schemas/
    │   ├── repositories/
    │   ├── services/
    │   └── api.py
    ├── agenda_escalas/                 # Contexto: Agenda & Escalas
    │   ├── models/
    │   │   └── agenda.py              # Models: TipoEvento, Evento, EventoRecorrencia,
    │   │                              #         EventoOcorrencia, EscalaMinisterioOcorrencia,
    │   │                              #         EventoDepartamento, EventoMinisterio, EventoMembro
    │   ├── schemas/
    │   ├── repositories/
    │   ├── services/
    │   └── api.py
    └── relatorios_historico/          # Contexto: Relatórios & Histórico
        ├── schemas/
        ├── services/
        └── api.py
```

---

## Variáveis de ambiente

Copie `.env.example` para `.env` e ajuste os valores:

```bash
cp .env.example .env
```

| Variável | Descrição | Exemplo |
|---|---|---|
| `DATABASE_URL` | URL usada dentro do Docker (host `db`) | `postgresql+asyncpg://ibmi:ibmi@db:5432/ibmi` |
| `ALEMBIC_DATABASE_URL` | URL para uso local fora do Docker (host `localhost`) | `postgresql+asyncpg://ibmi:ibmi@localhost:5432/ibmi` |
| `SECRET_KEY` | Chave para assinar tokens JWT | Gerar com o comando abaixo |
| `ALGORITHM` | Algoritmo JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Validade do access token | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Validade do refresh token | `7` |
| `DEBUG` | Habilita echo SQL no SQLAlchemy | `false` |
| `ALLOWED_ORIGINS` | Origens permitidas no CORS (JSON array) | `["http://localhost:3000"]` |

Gerar `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

> **Importante:** `ALEMBIC_DATABASE_URL` é usada tanto pelo Alembic quanto pelo uvicorn
> quando rodando fora do Docker. A aplicação resolve automaticamente:
> se `ALEMBIC_DATABASE_URL` estiver definida, ela tem prioridade sobre `DATABASE_URL`.

---

## Como rodar (desenvolvimento local)

### Pré-requisitos

- Python 3.12+
- Docker e Docker Compose

### 1. Criar e ativar o ambiente virtual

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# ou
.venv\Scripts\activate         # Windows
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Editar .env: ajustar SECRET_KEY e confirmar as URLs
```

### 4. Subir apenas o banco de dados

```bash
docker compose up db -d
# Aguardar o banco ficar saudável:
docker compose ps
```

### 5. Aplicar as migrações

```bash
alembic upgrade head
```

### 6. Criar o primeiro usuário ADMIN

```bash
python scripts/create_admin.py
```

O script aceita entrada interativa ou variáveis de ambiente:

```bash
ADMIN_EMAIL=admin@ibmi.app ADMIN_PASSWORD=s3nh@F0rte python scripts/create_admin.py
```

### 7. Rodar o servidor

```bash
uvicorn app.main:app --reload
```

API disponível em `http://localhost:8000`
Documentação interativa em `http://localhost:8000/docs`

---

## Como rodar (Docker completo)

```bash
# Subir todos os serviços (db + backend)
docker compose up -d

# Aplicar migrações dentro do container
docker compose exec backend alembic upgrade head

# Criar primeiro ADMIN dentro do container
docker compose exec backend python scripts/create_admin.py

# Acompanhar logs
docker compose logs -f backend
```

---

## Fluxo de trabalho com Alembic

```
Editar model SQLAlchemy
        ↓
alembic revision --autogenerate -m "descricao"
        ↓
Revisar o arquivo gerado em alembic/versions/
        ↓
alembic upgrade head
```

Comandos úteis:

```bash
alembic current      # status das migrações
alembic history      # histórico
alembic downgrade -1 # reverter última
alembic downgrade base # reverter todas
```

---

## Endpoints de autenticação (Bloco 2 — implementado)

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | público | Retorna access + refresh token |
| `POST` | `/api/v1/auth/refresh` | público | Renova tokens (rotação) |
| `POST` | `/api/v1/auth/logout` | autenticado | Revoga refresh token |
| `POST` | `/api/v1/auth/register` | ADMIN | Cria novo usuário |
| `GET` | `/api/v1/auth/me` | autenticado | Dados do usuário atual |

---

## Decisões de arquitetura relevantes

| Decisão | Escolha | Motivo |
|---|---|---|
| **Usuario × Membro** | Entidades separadas | Admin pode existir sem ser membro; membro pode existir sem acesso ao sistema |
| **Migrations** | Alembic auto-generate | Gera DDL a partir dos models, evita escrita manual de SQL |
| **Engine** | SQLAlchemy 2.0 async (asyncpg) | Compatível com FastAPI async por padrão |
| **Timestamps** | `TimestampMixin` em `shared/mixins.py` | Reutilizável em todos os contextos |
| **ALEMBIC_DATABASE_URL** | Variável com prioridade sobre `DATABASE_URL` | Permite rodar localmente sem alterar URL do Docker |
| **Refresh token** | Hash SHA-256 no banco, 1 sessão/usuário | Segurança suficiente + logout real sem over-engineering |
| **Hash de senha** | `bcrypt` direto (sem passlib) | Compatível com bcrypt 4+/5+; passlib não acompanhou API |
| **Registro** | Restrito a ADMIN autenticado | Controle total sobre quem acessa o sistema |
| **Primeiro ADMIN** | CLI Python (`scripts/create_admin.py`) | Seguro, explícito, sem expor rota pública |

---

## Próximos passos

- [ ] **Bloco 3** — CRUDs por contexto: `estrutura_eclesiastica` → `pessoas_ministerios` → `agenda_escalas`
- [ ] **Bloco 4** — Regras de visibilidade e geração de ocorrências a partir de recorrência
