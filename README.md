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
## Sincronização de Oportunidades com o Google Drive

As planilhas de oportunidades (uma Planilha Google por área, sobrescrita semanalmente)
são importadas automaticamente toda segunda-feira às 06h (Brasília) pelo workflow
`.github/workflows/sync_oportunidades.yml`, que executa `drive_sync.py`. Na página
**Oportunidades → Importação** (ADMIN) é possível cadastrar a planilha de cada área e
sincronizar manualmente. Uma planilha só é reimportada se tiver sido alterada no Drive.

Configuração (uma única vez):

1. No [Google Cloud Console](https://console.cloud.google.com/), crie um projeto e ative a **Google Drive API**.
2. Em *IAM e administrador → Contas de serviço*, crie uma Service Account e gere uma chave **JSON**.
3. No Google Drive, compartilhe cada planilha (ou a pasta que as contém) como **Leitor** com o e-mail da Service Account (`...@...iam.gserviceaccount.com`).
4. Nos secrets do Streamlit Cloud, adicione `GDRIVE_SA_JSON` com o conteúdo do JSON (como string, entre aspas triplas).
5. No GitHub, em *Settings → Secrets and variables → Actions*, crie os secrets `DATABASE_URL` e `GDRIVE_SA_JSON`.
6. No app, cadastre o link da planilha de cada área e use **Sincronizar com Drive** para testar. O workflow também pode ser disparado manualmente em *Actions → Run workflow*.

# Consulta_editais
