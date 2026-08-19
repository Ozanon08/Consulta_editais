# Portal de Editais em Streamlit

Aplicação Streamlit para consulta de editais com:

- login de usuários
- perfis de acesso por papel
- gestão de usuários
- solicitação de busca de novos temas
- painel administrativo de solicitações
- substituição da base por nova planilha Excel
- filtros, detalhe, resumo e exportação CSV



## Observações

- O banco utilizado é SQLite, ideal para uma primeira versão local.
- Para uso multiusuário em produção, vale migrar para PostgreSQL.
- A coluna `Serviços` é normalizada em tabela associativa para melhorar filtros e consistência.
# Consulta_editais
