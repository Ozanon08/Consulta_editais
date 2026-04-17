# Portal de Editais em Streamlit

Aplicação Streamlit para consulta de editais com:

- login de usuários
- perfis de acesso por papel
- gestão de usuários
- solicitação de busca de novos temas
- painel administrativo de solicitações
- substituição da base por nova planilha Excel
- filtros, detalhe, resumo e exportação CSV

## Perfis

- **ADMIN**: acesso total
- **PMO**: acesso total, exceto criação de novos usuários
- **COORDENADOR**: pode consultar tudo e solicitar inclusão de temas, mas não pode substituir a base
- **GERAL**: apenas visualização das tabelas e filtros

## Usuário inicial

- **Usuário:** `ADMIN`
- **Senha:** `ADMIN123`

Altere ou crie novos usuários após o primeiro acesso.

## Como executar

```bash
pip install -r requirements.txt
python load_data.py
streamlit run app.py
```

## Estrutura principal

- `app.py`: aplicação Streamlit
- `schema.sql`: estrutura SQLite completa
- `load_data.py`: carga da planilha Excel para o banco
- `Modelo dados.xlsx`: base inicial
- `editais.db`: banco SQLite gerado localmente

## Observações

- O banco utilizado é SQLite, ideal para uma primeira versão local.
- Para uso multiusuário em produção, vale migrar para PostgreSQL.
- A coluna `Serviços` é normalizada em tabela associativa para melhorar filtros e consistência.
# Consulta_editais
