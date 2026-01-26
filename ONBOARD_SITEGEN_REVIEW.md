# Revisão: Onboarding & Gerador de Site (CRM)

Escopo: análise do fluxo de onboarding e do serviço de geração de site por IA no repositório `innexar-crm`. O relatório será atualizado incrementalmente com cada arquivo/análise adicional.

Status atual: análise inicial concluída para os seguintes arquivos:
- backend/app/services/site_generator_service.py
- backend/app/models/site_order.py
- backend/app/api/site_orders.py
- backend/app/api/site_customers.py
- backend/app/api/customer_auth/routes.py
- backend/app/services/ai_service.py
- backend/migrations/add_onboarding_columns.py

**Resumo executivo (problemas de maior impacto)**
- Risco de path traversal e escrita arbitrária ao gravar arquivos gerados pela IA em `SiteGeneratorService`.
- Falta de validação estrita do JSON retornado pela IA (schema + limites de tamanho/quantidade).
- Uso de CWD (`os.getcwd()`) para construir `generated_sites` — comportamento dependente do processo e potencial inseguro.
- Possibilidade de condições de corrida/duplicação no webhook Stripe (criação de pedidos) sem tratamento robusto de IntegrityError.
- Tratamento amplo de exceções que pode ocultar falhas críticas (ex.: `_log_progress` silencia erros).

---

## Achados por arquivo

### `backend/app/services/site_generator_service.py`
- _Log de progresso_ (`_log_progress`): usa SQL cru com `json.dumps(details)`; se a coluna for JSONB, o valor pode ser double-encoded. Exceções são logadas e engolidas — pode ocultar falhas de persistência.
- _Fluxo principal_ (`generate_site`): boas fases (strategy, fetch, prompt, AI, parse, write). Pontos críticos:
  - `generate_strategy_brief` tem exceção capturada e suprimida; `briefing` pode ficar indefinido.
  - Busca de `order` e `onboarding` correta, mas não há verificação explícita de permissões multi-tenant.
  - `AI.generate` assume que `AIService` retorna dict com `content` — `ai_service` tem essa convenção, porém formatos variam por provedor.
  - Parsing do conteúdo AI: tenta extrair blocos fence ```json``` ou ``` — demasiado frágil; nenhum schema/whitelist é aplicado.
  - Path traversal: `file['path']` escrito diretamente em `target_dir` sem `normpath`/validação — risco de sobrescrever arquivos fora do diretório.
  - `target_dir` baseado em `os.getcwd()` — não é previsível; sugiro `tempfile.mkdtemp()` ou caminho configurável.
  - Falta de validação de tamanho/contagem de arquivos; limite para evitar DoS.
  - Atualização de status e commit são feitos após escrita em disco mas sem transação que englobe escrita em FS + BD.

Recomendações imediatas:
- Sanitizar `file['path']` com `os.path.normpath` e garantir `final_path.startswith(target_dir)`.
- Usar `tempfile` para escrita atômica e mover para destino somente após validação completa.
- Validar `project_data` contra um schema pydantic (ex.: `files: List[FileSpec]`) e aplicar limites (max_files, max_size_per_file).
- Persistir logs via modelo `SiteGenerationLog` ou usar parâmetros para JSONB.
- Tornar `generate_strategy_brief` falha explícita ou retornar placeholder consistente.


### `backend/app/models/site_order.py`
- Modelos e enums bem definidos; `SiteOnboarding` cobre o fluxo de 7 passos.
- Atenção: vários campos `nullable=False` (ex.: `business_phone`, `primary_city`, `primary_service`) exigem validação no frontend. Migrar dados históricos pode falhar se houver registros faltantes.
- `order.onboarding` é one-to-one com `unique=True` em `order_id` — boa garantia.

Recomendações:
- Adicionar `cascade="all, delete-orphan"` se for desejado remover onboarding ao deletar pedidos.
- Definir limites de tamanho (VARCHAR lengths) para alguns campos longos para mitigar inserção de blobs.


### `backend/app/api/site_orders.py`
- Endpoint `POST /{order_id}/onboarding` delega para `OnboardingService.process_onboarding` — revisar esse serviço (próximo passo).
- Webhook Stripe (`/webhook`): cria pedido quando não existe. Possíveis problemas:
  - Se dois webhooks paralelos chegarem, ambos podem tentar criar o mesmo `stripe_session_id`. Embora `stripe_session_id` seja `unique=True`, não há captura de `IntegrityError` no commit para tornar o fluxo idempotente.
  - Uso de `print` para logs e mensagens debug — considerar logger estruturado.
- `trigger_build` inicia geração em background via `background_tasks.add_task` com `asyncio.run` envolvendo `AsyncSessionLocal`:
  - `asyncio.run` dentro de um worker é aceitável, mas cuidado com ambientes (uvicorn worker) — testes de carga necessários.
  - `order.status` é atualizado para `GENERATING` e commitado antes de iniciar job — bom, porém sem rollback se geração falhar.

Recomendações:
- Envolver criação de pedido via webhook com try/except IntegrityError e implementar idempotência robusta.
- Trocar `print` por `logger`.
- Considerar uso de um worker (Celery/RQ) ou um background task que não invoque `asyncio.run` em runtime de servidor web.


### `backend/app/api/site_customers.py` e `backend/app/api/customer_auth/routes.py`
- Fluxos de autenticação e gerenciamento de clientes estão coerentes. JWT de cliente com `SECRET_KEY` e 1 semana de validade.
- Função `create_customer_account` gera e faz `await db.flush()` mas não `commit` — isso é intencional para permitir transação composta; verificar chamadores para garantir commit.
- Tratamento de tokens (reset/verify) implementado com prazos e debounce razoáveis.

Recomendações:
- Certificar que tokens secretos e `SECRET_KEY` estejam seguros (variáveis de ambiente). Evitar expor `temp_password` em logs ou emails.
- Usar `logger` ao invés de prints em endpoints relacionados para uniformizar auditoria.


### `backend/app/services/ai_service.py`
- `AIService` faz roteamento por `AITaskRouting` e suporta múltiplos providers; padrão de fallback é implementado.
- Possíveis fragilidades:
  - `_call_openai` assume a estrutura `data['choices'][0]['message']['content']` — se o provider retornar diferente, `generate` será capturado e fallback pode ser tentado, porém falta validação do conteúdo.
  - Timeouts fixed em `httpx.AsyncClient(timeout=120.0)` — OK, mas talvez configurar via `AIConfig` seja melhor.
  - Alguns providers retornam formatos distintos; `generate` apenas retorna `{'content': ...}` sem metadados (tokens used etc.).

Recomendações:
- Padronizar resposta de `AIService` com um schema: `{content: str, provider: str, raw: dict}`.
- Validar `content` e sanitizar antes de repassar para `site_generator_service`.
- Extrair timeouts e outras opções para `AIConfig`.


### `backend/migrations/add_onboarding_columns.py`
- Migration script adiciona colunas necessárias; usa `information_schema` checks antes de `ALTER TABLE` — robusto para reexecução.
- Atenção: usa `VARCHAR NULL` sem length — Postgres aceitará, mas talvez prefira `VARCHAR(255)`.

Recomendações:
- Testar migration em staging; considerar definir lengths e defaults explicitamente onde aplicável.

---

## Próximos passos que vou executar (se confirmar):
- Fazer análise linha-a-linha do serviço `OnboardingService` (`backend/app/services/onboarding_service.py`) e de `OrderRepository` e `SiteDeliverable`.
- Adicionar validações/patches sugeridos no `SiteGeneratorService` (sanitização de paths, schema pydantic, uso de `tempfile`).
- Gerar PR-ready patches com testes unitários (se você aprovar).

Vou continuar a analisar `OnboardingService` e repositórios relacionados agora, e adicionarei os achados neste mesmo relatório.

---

### `backend/app/services/onboarding_service.py` (novos achados)
- Tipagem inconsistente: `process_onboarding(self, order_identifier: str, onboarding_data: dict)` declara `onboarding_data` como `dict`, mas o endpoint passa um Pydantic `SiteOnboardingCreate` (com `model_dump()` usado internamente). Melhor declarar o tipo como o Pydantic model ou aceitar `Any`/`BaseModel` para clareza.
- Mass assignment: o código faz `**{k: v for k, v in onboarding_data.model_dump().items() if k != "password"}` e passa direto ao construtor `SiteOnboarding`. Risco de campos inesperados/extra ou campos mal formatados; recomendo usar `SiteOnboardingCreate` validações explícitas e um `model_dump`/`dict(exclude_none=True)` controlado.
- Concurrency/race: verifica `order.onboarding_completed_at` antes de inserir; em submissões paralelas isso pode permitir duas tentativas simultâneas. Como `order_id` é `UNIQUE` em `site_onboardings`, a segunda inserção causará `IntegrityError` — isso é tratado em `_handle_customer_account` mas não ao criar o `SiteOnboarding`. Recomendo envolver criação do onboarding em try/except IntegrityError com rollback e resposta amigável (idempotência).
- Criação do `Onboarding`: faz `self.db.add(onboarding)` e só dá `await self.db.commit()` ao final. Se `_handle_customer_account` levantar `IntegrityError`, o código faz `await self.db.rollback()` dentro do handler e retorna 409 — porém a criação do onboarding pode ter sido parcialmente aplicada; revisar fluxo de transações para garantir consistência.
- `_handle_customer_account`: captura `IntegrityError` ao criar conta cliente e faz `await self.db.rollback()` — isto reverte todas as alterações no mesmo sessão, inclusive a criação de `onboarding` feita antes. Isso pode ser desejado, porém o usuário receberá 409 (email duplicado) e o onboarding não será salvo. Boa prática, mas documentar o comportamento.
- Geração IA em background: usa `background_tasks.add_task(run_generation_sync, order_id)` com `asyncio.run` wrapper — repetir aviso: `asyncio.run` em determinados servidores pode causar problemas se chamado dentro de um loop existente ou com threads; recomenda-se mover para um worker (Celery/RQ) ou usar `anyio`/`trio` compatível com FastAPI/uvicorn.

Recomendações imediatas para `OnboardingService`:
- Atualizar assinatura para aceitar `SiteOnboardingCreate` ou validar `onboarding_data` antes de `**`-unpack.
- Envolver criação de `SiteOnboarding` em try/except IntegrityError para retornar um erro idempotente quando já existe onboarding.
- Evitar mass-assignment direto; mapear explicitamente campos permitidos ou use `SiteOnboardingCreate.model_dump(exclude_none=True)` com um whitelist.
- Considerar extrair o trigger de geração IA para um job queue externo.


### `backend/app/repositories/order_repository.py` (novos achados)
- `find_by_identifier`: usa `func.right(SiteOrder.stripe_session_id, 8)` — dependendo do backend/PG version isso funciona, mas considere usar `substring` ou criar uma functional index para performance. Comentário já faz menção.
- `get_logs` usa `text("SELECT * FROM site_generation_logs ...")` e itera `for row in result:` assumindo atributos (`row.id`). Isso funciona com Row objects, porém se a query crescer de volume, paginar/limitar resultados é recomendado.
- Falta cache/pagination em `get_logs` e não há proteção contra leitura de logs muito grandes (DoS). Também falta ordenação por `created_at` explicitamente (embora query already uses ORDER BY).

Recomendações imediatas para `OrderRepository`:
- Adicionar paginação (limit/offset) e opcional filtro por etapas/status em `get_logs`.
- Considerar retornar registros como dicionários (`row._mapping`) para evitar depender de atributos dinâmicos.


### `backend/app/models/site_deliverable.py` (novos achados)
- `SiteDeliverable.content` é `Text` e pode armazenar longos conteúdos (briefings, markdown). Ok, mas para entregáveis grandes de código/ZIPs, considerar armazenar artefatos em storage (S3) e salvar links em `metadata_json`.
- `type` e `status` usam Enum SQL types — bom. `order = relationship("SiteOrder", back_populates="deliverables")` complementa o `SiteOrder.deliverables`.

Recomendações imediatas:
- Se forem gerar código grande (arquivo zip), prefira salvar em storage externo e colocar link em `metadata_json`.

---

Atualizei o relatório com estes achados; agora vou analisar os arquivos relacionados a `site_generation_logs` (migration/model) e `AIService` rota de fallback/formatting em mais detalhes em seguida.
