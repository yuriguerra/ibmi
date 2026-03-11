## Visão Geral

Sistema de agenda para igrejas, focado em:
- cadastro de pessoas e estrutura eclesiástica (igrejas, congregações, departamentos, ministérios)
- organização de eventos (incluindo recorrência avançada)
- escalas de ministérios por ocorrência de evento
- visualização de agenda filtrável (calendário + lista/timeline)

Instalação por organização (ex.: uma igreja sede ou convenção), permitindo múltiplas igrejas/congregações internas na mesma instância.

Stack alvo:
- **Frontend**: aplicação web responsiva (SPA/SSR)
- **Backend**: Python + FastAPI (monólito modular)
- **Banco de dados**: PostgreSQL
- **Deployment**: 3 containers (frontend, backend, db) por instalação

---

## Requisitos do Sistema

### Requisitos Funcionais

- **RF1 – Cadastro de Igrejas/Congregações**
  - Cadastrar igrejas e congregações dentro de uma mesma organização.
  - Diferenciar matriz/congregação e, opcionalmente, vincular congregações à igreja mãe.

- **RF2 – Cadastro de Departamentos**
  - Cadastrar departamentos por igreja (ex.: infância, jovens, louvor, diaconia).
  - Relacionar departamentos à igreja a que pertencem.

- **RF3 – Cadastro de Ministérios**
  - Cadastrar ministérios por igreja (ex.: ministério de louvor, intercessão, recepção).
  - Usados para construção de escalas de serviço nos eventos.

- **RF4 – Cadastro de Membros**
  - Informações mínimas:
    - nome completo
    - data de nascimento
    - email
    - telefone
    - status (ex.: ativo, em observação, desligado)
    - igreja principal
  - Relacionar membros a múltiplos departamentos (N:N).
  - Relacionar membros a múltiplos ministérios (N:N), opcionalmente com função/observações.

- **RF5 – Tipos/Categorias de Evento**
  - Cadastrar tipos de evento (ex.: culto, ensaio, reunião, congresso).
  - Opcionalmente associar cor/ícone para destaque visual no calendário.

- **RF6 – Cadastro de Eventos**
  - Criar eventos vinculados a uma igreja/congregação.
  - Definir:
    - título, descrição, local
    - tipo/categoria (opcional)
    - data/hora de início e fim
    - visibilidade (geral ou restrita)

- **RF7 – Recorrência de Eventos (Avançada)**
  - Suportar recorrências:
    - diária
    - semanal (com intervalo: 1 semana, 2 semanas, etc.)
    - mensal
    - “todo primeiro domingo do mês”
    - “sexta-feira a cada duas semanas”
    - “todo dia 15”
  - Permitir definir data final ou número máximo de ocorrências.
  - Permitir ajustes pontuais em ocorrências individuais (horário diferente, cancelamento, etc.).

- **RF8 – Escala de Ministérios por Ocorrência**
  - Definir escala de serviço por **ocorrência concreta** do evento.
  - Relacionar:
    - ocorrência de evento
    - ministério
    - membro
    - papel (ex.: líder de louvor, músico, intercessor, recepcionista)
    - status (PENDENTE, CONFIRMADO, CANCELADO, SUBSTITUTO)
  - Permitir copiar a escala de uma ocorrência para outras (ex.: todas as sextas do mês).

- **RF9 – Visibilidade de Eventos**
  - Cada evento/ocorrência pode ser:
    - **GERAL** (visível a todos)
    - restrito por departamento (um ou vários)
    - restrito por ministério (um ou vários)
    - restrito a membros específicos (lista de membros)
  - Aplicar regras de visibilidade tanto no calendário quanto na lista/timeline.

- **RF10 – Perfis de Acesso**
  - **Admin/Líder**:
    - CRUD completo de cadastros (membros, igrejas, departamentos, ministérios, tipos de evento).
    - CRUD de eventos, recorrências e escalas.
    - Acesso a todos os relatórios.
  - **Membro**:
    - Acesso somente à visualização de agenda (calendário + lista/timeline), respeitando visibilidade.
    - Pode ver onde está escalado para servir.

- **RF11 – Visualização de Agenda**
  - Visualização em **calendário** (mês/semana/dia), estilo Google Calendar.
  - Visualização em **lista/timeline** de eventos futuros.
  - Permitir alternar entre modos de visualização.

- **RF12 – Filtros da Agenda**
  - Filtrar eventos/ocorrências por:
    - membro
    - departamento
    - ministério (possível extensão futura)
    - igreja/congregação
    - tipo/categoria de evento
  - Combinar filtros (ex.: “Eventos do Departamento X na Congregação Y no próximo mês”).

- **RF13 – Histórico e Relatórios**
  - Preservar histórico de eventos passados e escalas.
  - Permitir relatórios, por exemplo:
    - eventos realizados em um período por igreja/tipo
    - membros que serviram em determinado ministério em um período

---

### Requisitos Não Funcionais

- **RNF1 – Plataforma**
  - Aplicação web responsiva (desktop e mobile via navegador).
  - Backend em Python + FastAPI.
  - Banco de dados PostgreSQL.

- **RNF2 – Escala**
  - Porte esperado por instalação: até ~300 membros, poucos usuários simultâneos.
  - Arquitetura não precisa de alta disponibilidade complexa neste estágio.

- **RNF3 – Segurança Básica**
  - Autenticação com senha forte.
  - Toda a comunicação externa deve ser feita via HTTPS.
  - Separação de perfis admin/líder e membro.

- **RNF4 – Disponibilidade**
  - Quedas ocasionais de algumas horas são aceitáveis em situações raras.
  - Foco em simplicidade operacional em vez de alta disponibilidade avançada.

- **RNF5 – Extensibilidade Futura**
  - Prever:
    - notificações externas (e-mail, WhatsApp) como fase futura;
    - possíveis integrações com calendários externos (iCal/Google Calendar);
    - evolução de papéis/perfis de acesso.

---

## Modelo de Domínio (Visão Lógica)

### Entidades Principais

- **Igreja**
  - Representa uma igreja ou congregação dentro da organização.
  - Campos principais:
    - `id`
    - `nome`
    - `endereço` (opcional)
    - `tipo` (ex.: MATRIZ, CONGREGAÇÃO)
    - `igreja_mae_id` (opcional, para congregações ligadas a uma matriz)

- **Departamento**
  - Representa um departamento dentro de uma igreja específica.
  - Campos principais:
    - `id`
    - `igreja_id`
    - `nome`
    - `descricao`

- **Ministério**
  - Representa um ministério dentro de uma igreja específica (focado em escala).
  - Campos principais:
    - `id`
    - `igreja_id`
    - `nome`
    - `descricao`

- **Membro**
  - Pessoa cadastrada no sistema.
  - Campos principais:
    - `id`
    - `nome_completo`
    - `data_nascimento`
    - `email`
    - `telefone`
    - `status`
    - `igreja_principal_id`

- **Relações de Membro**
  - `membro_departamento` (N:N):
    - `membro_id`
    - `departamento_id`
  - `membro_ministerio` (N:N):
    - `membro_id`
    - `ministerio_id`
    - `funcao` (opcional)

- **Tipo de Evento**
  - Classifica eventos (ex.: culto, ensaio, reunião).
  - Campos principais:
    - `id`
    - `nome`
    - `cor` (opcional)
    - `descricao`

### Eventos e Recorrência

- **Evento (Mestre)**
  - Define o “template” do evento.
  - Campos principais:
    - `id`
    - `igreja_id`
    - `titulo`
    - `descricao`
    - `local`
    - `tipo_evento_id` (opcional)
    - `data_hora_inicio`
    - `data_hora_fim`
    - `e_recorrente` (bool)
    - `visibilidade` (enum: GERAL, POR_DEPARTAMENTO, POR_MINISTERIO, POR_MEMBRO)

- **Regra de Recorrência (`evento_recorrencia`)**
  - Campos principais:
    - `evento_id`
    - `frequencia` (DAILY, WEEKLY, MONTHLY, etc.)
    - `intervalo` (ex.: 1 = toda semana; 2 = a cada 2 semanas)
    - `dias_semana` (lista, ex.: [FRI] para “toda sexta”)
    - `dias_mes` (lista, ex.: [15] para “dia 15”)
    - `posicao_na_semana` (ex.: 1 = primeiro domingo; 3 = terceira quinta)
    - `data_fim` ou `ocorrencias_max`

- **Ocorrência Concreta de Evento (`evento_ocorrencia`)**
  - Representa um dia/hora específico no calendário.
  - Campos principais:
    - `id`
    - `evento_id`
    - `data_hora_inicio`
    - `data_hora_fim`
    - campos opcionais para overrides (ex.: `cancelado`, `nota_ocorrencia`)
  - Base da agenda (calendário + lista/timeline).

### Visibilidade de Eventos

- **Associações de Visibilidade**
  - `evento_departamento`:
    - `evento_id`
    - `departamento_id`
  - `evento_ministerio`:
    - `evento_id`
    - `ministerio_id`
  - `evento_membro`:
    - `evento_id`
    - `membro_id`

Regras de acesso (resumo):
- **Admin/Líder**:
  - Vê todas as ocorrências de todos os eventos da organização.
- **Membro**:
  - Vê:
    - eventos com `visibilidade = GERAL`
    - eventos associados a seus departamentos (`evento_departamento`)
    - eventos associados a seus ministérios (`evento_ministerio`)
    - eventos onde está explicitamente listado (`evento_membro`)

### Escala de Ministérios

- **Escala por Ocorrência (`escala_ministerio_ocorrencia`)**
  - Ligada à ocorrência, não apenas ao evento mestre.
  - Campos principais:
    - `id`
    - `evento_ocorrencia_id`
    - `ministerio_id`
    - `membro_id`
    - `papel`
    - `status` (PENDENTE, CONFIRMADO, CANCELADO, SUBSTITUTO)
    - `observacoes` (opcional)

---

## Arquitetura do Sistema

### Visão de Alto Nível

- **Frontend**
  - Aplicação web responsiva (SPA/SSR).
  - Módulos:
    - Autenticação
    - Cadastros (membros, igrejas, departamentos, ministérios, tipos de evento)
    - Agenda:
      - visualização em calendário (mês/semana/dia)
      - visualização em lista/timeline
      - filtros (membro, departamento, igreja, tipo)
    - Gestão de eventos:
      - criação/edição de evento mestre
      - definição de recorrência
      - gerenciamento de ocorrências pontuais
    - Gestão de escala de ministérios
    - Relatórios básicos

- **Backend (FastAPI – Monólito Modular)**
  - Contextos internos (módulos):
    - **Pessoas & Ministérios**
      - membros, ministérios, relações membro_departamento, membro_ministerio
    - **Estrutura Eclesiástica**
      - igrejas/congregações, departamentos
    - **Agenda & Escalas**
      - tipos de evento, eventos (mestre), regras de recorrência
      - ocorrências (evento_ocorrencia)
      - associações de visibilidade
      - escala de ministérios por ocorrência
    - **Relatórios & Histórico**
      - consultas agregadas e relatórios por período
  - Responsabilidades:
    - exposição de APIs REST/JSON (ou GraphQL, se adotado)
    - autenticação e autorização por perfil
    - aplicação das regras de visibilidade na consulta de agenda
    - geração e gerenciamento de ocorrências a partir das regras de recorrência

- **Banco de Dados (PostgreSQL)**
  - Um banco por instalação (por organização).
  - Todas as entidades lógicas descritas na seção de domínio mapeadas para tabelas relacionais.

### Deployment e Infraestrutura

- **Containers**
  - `frontend`:
    - Servidor de arquivos estáticos (ou runtime SSR) para o app web.
  - `backend`:
    - Aplicação FastAPI, exposta em porta HTTP interna/externa.
  - `db`:
    - PostgreSQL, com volume persistente para dados.

- **Orquestração**
  - Inicialmente via `docker-compose` ou equivalente:
    - uma stack por organização (um conjunto de 3 containers).
  - Possibilidade futura de:
    - escalar horizontalmente o backend
    - mover o Postgres para um serviço gerenciado

---

## Decision Log (Consolidado)

1. **Arquitetura Base**
   - **Decisão**: Backend monolítico modular em FastAPI + PostgreSQL, com frontend web separado.
   - **Alternativas**:
     - Microserviços independentes (serviço de membros, serviço de eventos, serviço de notificações).
     - Monólito sem fronteiras internas de contexto.
   - **Motivo**:
     - Simplicidade operacional + boa organização interna.
     - Preparar o terreno para extração futura de serviços, se necessário.

2. **Deployment em Containers**
   - **Decisão**: 3 containers por instalação (`frontend`, `backend`, `db`).
   - **Alternativas**:
     - Container único com tudo.
     - DB externo gerenciado desde o início.
   - **Motivo**:
     - Isolar responsabilidades e facilitar manutenção/escalabilidade básica.

3. **Escopo Multi-Igreja por Instância**
   - **Decisão**: Uma instância do sistema por organização, com múltiplas igrejas/congregações internas.
   - **Alternativas**:
     - Uma instância por igreja individual.
     - SaaS global multi-tenant com muitas organizações/igrejas no mesmo cluster de banco.
   - **Motivo**:
     - Balancear simplicidade de gestão com a necessidade de visão unificada da organização.

4. **Papéis e Permissões**
   - **Decisão**: Dois perfis iniciais:
     - `ADMIN/LEADER`: gestão completa de cadastros, eventos, recorrência, escala e relatórios.
     - `MEMBRO`: acesso de leitura à agenda e à própria escala.
   - **Alternativas**:
     - Papéis mais granulares (admin de congregação, líder de departamento, etc.).
   - **Motivo**:
     - Manter o sistema simples na v1 e evitar complexidade desnecessária de RBAC.

5. **Modelo de Eventos e Recorrência**
   - **Decisão**: Evento mestre + Regra de recorrência + Ocorrências concretas (`evento`, `evento_recorrencia`, `evento_ocorrencia`).
   - **Alternativas**:
     - Criar apenas eventos “flat”, sem mestre/recorrência.
     - Calcular recorrência somente on-the-fly, sem materializar ocorrências.
   - **Motivo**:
     - Suportar recorrência avançada com flexibilidade para edições pontuais por ocorrência.

6. **Escala de Ministérios por Ocorrência**
   - **Decisão**: Escalas ligadas diretamente às ocorrências (`escala_ministerio_ocorrencia`).
   - **Alternativas**:
     - Escala apenas no nível do evento mestre.
     - Escala apenas por ministério, sem associar ocorrência específica.
   - **Motivo**:
     - Refletir a realidade operacional (quem serve em qual dia) e viabilizar relatórios detalhados.

7. **Regras de Visibilidade**
   - **Decisão**:
     - Admin vê todos os eventos/ocorrências.
     - Membro vê:
       - eventos gerais
       - eventos onde seu departamento/ministério é alvo
       - eventos onde está explicitamente convidado.
   - **Alternativas**:
     - Visibilidade totalmente aberta (todos veem tudo).
     - Visibilidade apenas por igreja (sem filtro por departamento/ministério).
   - **Motivo**:
     - Permitir eventos restritos (liderança, ministérios específicos) sem elevar demais a complexidade.

8. **Preservação de Histórico**
   - **Decisão**: Não apagar eventos passados nem escalas; utilizá-los em relatórios.
   - **Alternativas**:
     - Purga periódica de eventos antigos.
   - **Motivo**:
     - Atender a necessidade explícita de relatórios históricos.

9. **Interfaces de Agenda**
   - **Decisão**: Oferecer calendário (mês/semana/dia) + lista/timeline, ambos baseados em `evento_ocorrencia`.
   - **Alternativas**:
     - Somente lista de eventos.
     - Somente calendário.
   - **Motivo**:
     - Calendário é central para a gestão de agenda, e a visão em lista facilita entendimento de próximos eventos.

---

## Riscos e Pontos de Atenção

- **Complexidade da Recorrência**
  - Regras do tipo “primeiro domingo do mês” + exceções pontuais podem ser fonte de bugs se a geração de ocorrências não for bem testada.
  - Estratégia recomendada:
    - gerar ocorrências para janelas de tempo (ex.: próximo mês) com revalidação constante
    - ter testes automatizados cobrindo casos de recorrência complexa.

- **UX de Escala**
  - A gestão de escala por ocorrência pode ser trabalhosa para o usuário se o fluxo não for bem projetado.
  - Importante prever:
    - clonagem de escala entre ocorrências
    - substituições ágeis (troca de membro)
    - destaque visual da escala no calendário.

- **Evolução de Perfis**
  - É provável que, no futuro, surja a necessidade de perfis mais finos (ex.: líder de um único departamento).
  - A camada de autorização deve ser desenvolvida com isso em mente, mesmo que inicialmente simples.

- **Integrações Futuras**
  - Integrações com WhatsApp, e-mail e calendários externos podem introduzir novos requisitos de segurança, consentimento e auditoria.