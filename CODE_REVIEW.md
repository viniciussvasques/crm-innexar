# Line-by-Line Code Review

## Backend

### FILE: app/services/stripe_service.py
### MUST-FIX
- Lines 86-88: `stripe.Webhook.construct_event` é uma operação síncrona (CPU-bound, crypto) sendo executada diretamente em uma função `async`. Isso bloqueia o Event Loop.
    - **Solução**: Executar em threadpool via `fastapi.concurrency.run_in_threadpool` ou `loop.run_in_executor`.
- Lines 18-23: `_load_config` cria uma `AsyncSessionLocal` manualmente se `db` não for fornecido. Isso pode causar vazamento de conexões se não monitorado ou se ocorrer exceção fora do `async with`.
    - **Solução**: Sempre injetar `db` via Dependência ou garantir que o Service seja instanciado com Sessão válida no Controller.

### FILE: app/api/auth.py
### SHOULD-FIX
- Line 15: O endpoint `/login` recebe `UserLogin` (JSON Body). O padrão OpenAPI/FastAPI espera `OAuth2PasswordRequestForm` (Form Data) para o botão "Authorize" do Swagger funcionar nativamente.
    - **Sugestão**: Migrar para `OAuth2PasswordRequestForm` ou manter customizado ciente da limitação do Swagger.

### FILE: app/api/site_orders.py
### SHOULD-FIX
- Lines 231-300 (Addons & Templates): Lógica de CRUD (Select, Insert, Update) implementada diretamente no Controller (`router`).
    - **Sugestão**: Mover para `OrderRepository` ou `ProductRepository`.
- Lines 211-226 (`get_onboarding`): Acesso direto ao DB (`db.execute`). Deveria usar Repository.

## Frontend

### FILE: src/app/site-orders/page.tsx
### MUST-FIX
- Componente excessivamente complexo (37KB+). Mistura lógica de negócio (cálculo de datas, mapeamento de status) com apresentação.
    - **Solução**: Extrair lógica para `hooks/useOrders.ts` e `hooks/useTimeline.ts`.
- Fetch de dados manual (`loadOrders`) em `useEffect` sem tratamento robusto de Cache/Revalidação.
    - **Sugestão**: Adotar React Query ou SWR.

### FILE: src/app/login/page.tsx
### NIT
- (Verificação pendente: confirmar se usa `api.post` com interceptor de erro global ou local)
