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
└── app/
    ├── main.py                         # Entrada FastAPI, lifespan, CORS
    ├── shared/
    │   ├── mixins.py                   # TimestampMixin (created_at, updated_at)
    │   └── all_models.py               # Importa todos os models (usado pelo Alembic)
    ├── core/
    │   ├── config.py                   # Settings via Pydantic Settings
    │   ├── database.py                 # SQLAlchemy 2.0 async, get_db
    │   └── security.py                 # JWT, hash de senha
    ├── api/
    │   ├── deps.py                     # Dependências compartilhadas (get_current_user)
    │   └── v1/
    │       └── router.py               # Agrega todos os routers
    ├── auth/                           # Contexto: Autenticação
    │   ├── models/
    │   │   └── usuario.py              # Model: Usuario (credenciais + perfil)
    │   ├── schemas/
    │   ├── services/
    │   └── api.py
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
| `DATABASE_URL` | URL do banco usada pela aplicação (host `db` = Docker) | `postgresql+asyncpg://ibmi:ibmi@db:5432/ibmi` |
| `ALEMBIC_DATABASE_URL` | URL usada pelo Alembic localmente (host `localhost`) | `postgresql+asyncpg://ibmi:ibmi@localhost:5432/ibmi` |
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

> **Importante:** `DATABASE_URL` aponta para `db` (hostname do container Docker).
> `ALEMBIC_DATABASE_URL` aponta para `localhost` (para rodar migrações fora do container).
> Ambas coexistem no mesmo `.env`.

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

### 4. Subir o banco de dados

```bash
docker compose up db -d
# Aguardar o banco ficar saudável:
docker compose ps
```

### 5. Aplicar as migrações

```bash
# Gerar migration (apenas quando houver mudanças nos models):
alembic revision --autogenerate -m "descricao_da_mudanca"

# Aplicar todas as migrações pendentes:
alembic upgrade head
```

### 6. Rodar o servidor

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

# Acompanhar logs
docker compose logs -f backend
```

---

## Fluxo de trabalho com Alembic

O Alembic gerencia a evolução do schema do banco. O fluxo padrão é:

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
# Ver status das migrações
alembic current

# Ver histórico de migrações
alembic history

# Reverter a última migração
alembic downgrade -1

# Reverter todas as migrações
alembic downgrade base
```

> **Atenção:** sempre revise o arquivo gerado pelo `--autogenerate` antes de aplicar.
> O Alembic não detecta automaticamente renomeações de colunas/tabelas — ele trata
> como DROP + CREATE, o que causa perda de dados.

---

## Decisões de arquitetura relevantes

| Decisão | Escolha | Motivo |
|---|---|---|
| **Usuario × Membro** | Entidades separadas | Admin pode existir sem ser membro; membro pode existir sem acesso ao sistema |
| **Migrations** | Alembic auto-generate | Gera DDL a partir dos models, evita escrita manual de SQL |
| **Engine** | SQLAlchemy 2.0 async (asyncpg) | Compatível com FastAPI async por padrão |
| **Timestamps** | `TimestampMixin` em `shared/mixins.py` | Reutilizável em todos os contextos |
| **ALEMBIC_DATABASE_URL** | Variável separada no `.env` | Permite rodar Alembic localmente sem alterar `DATABASE_URL` |

---

## Próximos passos

- [ ] **Bloco 2** — Auth: `POST /auth/login`, `POST /auth/refresh`, `POST /auth/register`, dependências `get_current_user` e `require_admin`
- [ ] **Bloco 3** — CRUDs por contexto: `estrutura_eclesiastica` → `pessoas_ministerios` → `agenda_escalas`
- [ ] **Bloco 4** — Regras de visibilidade e geração de ocorrências a partir de recorrência
