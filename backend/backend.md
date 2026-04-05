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
│       ├── 20260329_000000_add_refresh_tokens.py
│       └── 20260331_000000_add_soft_delete.py
├── scripts/
│   └── create_admin.py                 # CLI para criar primeiro usuário ADMIN
└── app/
    ├── main.py                         # Entrada FastAPI, lifespan, CORS
    ├── shared/
    │   ├── mixins.py                   # TimestampMixin, SoftDeleteMixin
    │   └── all_models.py               # Importa todos os models (usado pelo Alembic)
    ├── core/
    │   ├── config.py                   # Settings via Pydantic Settings
    │   ├── database.py                 # SQLAlchemy 2.0 async, get_db
    │   └── security.py                 # JWT, hash de senha (bcrypt direto, sem passlib)
    ├── api/
    │   ├── deps.py                     # get_current_user, require_admin, CurrentUser, AdminUser
    │   └── v1/
    │       └── router.py               # Agrega todos os routers
    ├── auth/                           # Contexto: Autenticação ✅
    │   ├── models/
    │   │   ├── usuario.py              # Model: Usuario (credenciais + perfil)
    │   │   └── refresh_token.py        # Model: RefreshToken (1 sessão por usuário)
    │   ├── schemas/
    │   │   └── auth.py                 # LoginRequest, RegisterRequest, TokenResponse, etc.
    │   ├── services/
    │   │   └── auth_service.py         # login, register, refresh, logout
    │   └── api.py                      # POST /login, /refresh, /logout, /register; GET /me
    ├── estrutura_eclesiastica/         # Contexto: Estrutura Eclesiástica ✅
    │   ├── models/
    │   │   └── igreja.py               # Models: Igreja, Departamento
    │   ├── schemas/
    │   │   └── estrutura.py            # Schemas: Igreja, Departamento
    │   ├── services/
    │   │   └── estrutura_service.py    # CRUD Igreja + Departamento, soft/hard delete
    │   └── api.py                      # Rotas CRUD + /permanente (LGPD)
    ├── pessoas_ministerios/            # Contexto: Pessoas & Ministérios ✅
    │   ├── models/
    │   │   └── membro.py               # Models: Membro, Ministerio, associações N:N
    │   ├── schemas/
    │   │   └── pessoas.py              # Schemas: Membro, Ministério, vínculos
    │   ├── services/
    │   │   └── pessoas_service.py      # CRUD Membro + Ministério, vínculos N:N, soft/hard delete
    │   └── api.py                      # Rotas CRUD + vínculos + /permanente (LGPD)
    ├── agenda_escalas/                 # Contexto: Agenda & Escalas 🔜
    │   ├── models/
    │   │   └── agenda.py               # Models: TipoEvento, Evento, EventoRecorrencia,
    │   │                               #         EventoOcorrencia, EscalaMinisterioOcorrencia,
    │   │                               #         EventoDepartamento, EventoMinisterio, EventoMembro
    │   ├── schemas/
    │   ├── services/
    │   └── api.py
    └── relatorios_historico/           # Contexto: Relatórios & Histórico 🔜
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
alembic current        # status das migrações
alembic history        # histórico
alembic downgrade -1   # reverter última
alembic downgrade base # reverter todas
```

---

## Endpoints implementados

### Auth (Bloco 2)

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | público | Retorna access + refresh token |
| `POST` | `/api/v1/auth/refresh` | público | Renova tokens (rotação) |
| `POST` | `/api/v1/auth/logout` | autenticado | Revoga refresh token |
| `POST` | `/api/v1/auth/register` | ADMIN | Cria novo usuário |
| `GET` | `/api/v1/auth/me` | autenticado | Dados do usuário atual |

### Estrutura Eclesiástica (Bloco 3)

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| `GET` | `/api/v1/estrutura-eclesiastica/igrejas` | autenticado | Lista igrejas ativas |
| `GET` | `/api/v1/estrutura-eclesiastica/igrejas/{id}` | autenticado | Detalhe de uma igreja |
| `POST` | `/api/v1/estrutura-eclesiastica/igrejas` | ADMIN | Cria igreja/congregação |
| `PATCH` | `/api/v1/estrutura-eclesiastica/igrejas/{id}` | ADMIN | Atualiza igreja |
| `DELETE` | `/api/v1/estrutura-eclesiastica/igrejas/{id}` | ADMIN | Soft delete |
| `DELETE` | `/api/v1/estrutura-eclesiastica/igrejas/{id}/permanente` | ADMIN | Hard delete (LGPD) |
| `GET` | `/api/v1/estrutura-eclesiastica/igrejas/{id}/departamentos` | autenticado | Lista departamentos da igreja |
| `GET` | `/api/v1/estrutura-eclesiastica/departamentos/{id}` | autenticado | Detalhe de departamento |
| `POST` | `/api/v1/estrutura-eclesiastica/departamentos` | ADMIN | Cria departamento |
| `PATCH` | `/api/v1/estrutura-eclesiastica/departamentos/{id}` | ADMIN | Atualiza departamento |
| `DELETE` | `/api/v1/estrutura-eclesiastica/departamentos/{id}` | ADMIN | Soft delete |
| `DELETE` | `/api/v1/estrutura-eclesiastica/departamentos/{id}/permanente` | ADMIN | Hard delete (LGPD) |

### Pessoas & Ministérios (Bloco 3)

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| `GET` | `/api/v1/pessoas-ministerios/ministerios` | autenticado | Lista ministérios (filtrável por `?igreja_id=`) |
| `GET` | `/api/v1/pessoas-ministerios/ministerios/{id}` | autenticado | Detalhe de ministério |
| `POST` | `/api/v1/pessoas-ministerios/ministerios` | ADMIN | Cria ministério |
| `PATCH` | `/api/v1/pessoas-ministerios/ministerios/{id}` | ADMIN | Atualiza ministério |
| `DELETE` | `/api/v1/pessoas-ministerios/ministerios/{id}` | ADMIN | Soft delete |
| `DELETE` | `/api/v1/pessoas-ministerios/ministerios/{id}/permanente` | ADMIN | Hard delete (LGPD) |
| `GET` | `/api/v1/pessoas-ministerios/membros` | autenticado | Lista membros (filtrável por `?igreja_id=` e `?status=`) |
| `GET` | `/api/v1/pessoas-ministerios/membros/{id}` | autenticado | Detalhe de membro |
| `POST` | `/api/v1/pessoas-ministerios/membros` | ADMIN | Cria membro |
| `PATCH` | `/api/v1/pessoas-ministerios/membros/{id}` | ADMIN | Atualiza membro |
| `DELETE` | `/api/v1/pessoas-ministerios/membros/{id}` | ADMIN | Soft delete |
| `DELETE` | `/api/v1/pessoas-ministerios/membros/{id}/permanente` | ADMIN | Hard delete (LGPD) |
| `POST` | `/api/v1/pessoas-ministerios/membros/{id}/departamentos` | ADMIN | Vincula membro a departamento |
| `DELETE` | `/api/v1/pessoas-ministerios/membros/{id}/departamentos/{dep_id}` | ADMIN | Remove vínculo membro-departamento |
| `POST` | `/api/v1/pessoas-ministerios/membros/{id}/ministerios` | ADMIN | Vincula membro a ministério (com função) |
| `DELETE` | `/api/v1/pessoas-ministerios/membros/{id}/ministerios/{min_id}` | ADMIN | Remove vínculo membro-ministério |

---

## Roadmap de implementação

### ✅ Bloco 1 — Fundação
- Estrutura de projeto, modelos SQLAlchemy, migration inicial, docker-compose, Alembic

### ✅ Bloco 2 — Autenticação
- Login, refresh token (hash SHA-256, 1 sessão/usuário), logout, registro (ADMIN), `/me`
- Dependências `get_current_user` e `require_admin`
- CLI `create_admin.py` para primeiro ADMIN

### ✅ Bloco 3 — CRUDs base
- `estrutura_eclesiastica`: Igreja (MATRIZ/CONGREGAÇÃO com validação), Departamento
- `pessoas_ministerios`: Membro, Ministério, vínculos N:N (membro-departamento, membro-ministério)
- Soft delete (`deleted_at`) + hard delete (`/permanente`) em todas as entidades principais
- Paginação `limit/offset` em todas as listagens
- Testes básicos em `tests/test_bloco3.py`

### 🔜 Bloco 3 — Pendências
- [ ] Configurar `conftest.py` com banco de teste para rodar `pytest`
- [ ] `pessoas_ministerios/schemas/__init__.py`
- [ ] `TipoEvento` — CRUD simples em `agenda_escalas`

### 🔜 Bloco 4 — Agenda & Escalas
- [ ] Criação e edição de Evento mestre
- [ ] Geração de ocorrências a partir de regras de recorrência
  - Suporte a: diária, semanal (com intervalo), mensal, "primeiro domingo do mês", "todo dia 15"
  - Data fim ou número máximo de ocorrências
- [ ] Overrides pontuais por ocorrência (cancelamento, horário diferente, nota)
- [ ] Escala de ministérios por ocorrência (CRUD + cópia entre ocorrências)
- [ ] Regras de visibilidade na consulta de agenda (GERAL, por departamento, ministério, membro)
- [ ] Endpoint de agenda com filtros (membro, departamento, ministério, igreja, tipo de evento)

### 🔜 Bloco 5 — Fechamento
- [ ] `relatorios_historico`: eventos realizados por período/igreja/tipo; membros por ministério
- [ ] Atualização final do `backend.md`
- [ ] Atualização final da coleção Postman

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
| **Soft delete** | Campo `deleted_at TIMESTAMPTZ` | Preserva histórico; `IS NULL` = ativo |
| **Hard delete** | Rota separada `DELETE /{id}/permanente` | Atende LGPD sem expor operação destrutiva no fluxo normal |
| **Paginação** | `limit/offset` em todas as listagens | Simples e suficiente para o porte (~300 membros) |
| **Padrão de camadas** | Service + Router (sem repository) | Separa HTTP de negócio sem burocracia desnecessária para o porte |