# System Architecture

## Visão Geral
O Innexar CRM é uma plataforma SaaS para construção de sites assistida por IA.
Arquitetura monolítica em serviços (Frontend Next.js + Backend FastAPI).

## Fluxo de Dados
1.  **Frontend (Next.js)**: Interface do usuário. Consome API via Axios.
2.  **API Gateway (FastAPI)**: Recebe requisições, valida Auth (JWT), orquestra serviços.
3.  **Database (PostgreSQL)**: Armazena Tenants, Users, Orders, AI Configs.
4.  **Cache/Queue (Redis)**: Filas de tarefas assíncronas (IA generation) e cache.
5.  **External**:
    - **Stripe**: Pagamentos e Assinaturas.
    - **AI Providers**: OpenAI, Anthropic, etc. (Via Backend Proxy).

## Fluxo de IA
1.  Frontend solicita geração (ex: sitemap, copy).
2.  Backend valida quotas e seleciona Provider (Router Logic).
3.  Req para Provider (ex: OpenAI).
4.  Resposta processada e salva no banco.
5.  Frontend recebe resultado (Polling ou WebSocket TBD).

## Pipeline (Onboarding -> Deploy)
1.  **Landing**: Usuário escolhe plano.
2.  **Checkout**: Stripe Subscription.
3.  **Webhook**: Stripe confirma pagamento -> Backend cria Tenant/User.
4.  **Onboarding**: Usuário preenche form (Nicho, Cores).
5.  **Provisioning**: Backend inicia Tasks de IA para gerar site.
6.  **Deploy**: Servidor recebe arquivos (SSH/FTP) e publica.

## Pontos Críticos
-   **Auth**: JWT Stateless. Tokens de IA criptografados no banco.
-   **Webhooks**: Devem ser idempotentes (Stripe).
-   **AI Costs**: Monitoramento de tokens por Tenant.
-   **Security**: `api_key` de provedores nunca expostas no client.
