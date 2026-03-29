---

## Próximos Passos Sugeridos

1. Definir a estrutura inicial de pastas do backend FastAPI por contexto (Pessoas & Ministérios, Estrutura Eclesiástica, Agenda & Escalas, Relatórios).
2. Especificar o schema SQL detalhado para PostgreSQL com base nas entidades desta definição.
3. Projetar os principais endpoints da API (rotas FastAPI) para:
   - cadastros básicos
   - criação/edição de eventos e recorrências
   - geração e consulta de ocorrências
   - gestão de escalas
   - leitura de agenda (calendário + lista) com filtros e visibilidade.
4. Definir formato padrão para export/integração de calendário (iCal) e planejar a futura integração com WhatsApp.