# Fluxo Manual de Sites + IA de Planejamento

## 1. Visão Geral

- **Objetivo**: cliente paga, faz onboarding/briefing, equipe constrói o site manualmente, IA ajuda apenas em planejamento e conteúdo de páginas (não em código).
- **Componentes principais**:
  - CRM (`Site Orders`): pipeline, briefing, produção, comunicação, entregáveis.
  - Portal do cliente: acompanha status, envia feedbacks, vê preview.
  - IA: gera documentos de apoio (briefing, sitemap, rascunhos de conteúdo, SEO).

## 2. Pipeline de Status (CRM)

1. `pending_payment` – aguardando pagamento.
2. `paid` – pagamento confirmado.
3. `onboarding_pending` – cliente ainda não preencheu onboarding.
4. `briefing` – onboarding completo, aguardando equipe revisar.
5. `building` – equipe construindo site em staging.
6. `preview` – preview enviado ao cliente, aguardando revisão.
7. `review` – ajustes em andamento.
8. `delivered` – site final entregue.
9. `cancelled` – cancelado/reembolsado.

## 3. Modal de Pedido (Order Details)

### 3.1. Overview

- **Status & ações**:
  - `paid`: botão **Start Manually** (vai para `building`) ou fluxo direto conforme necessidade.
  - `briefing`: botão **Start Development** (vai para `building`).
  - `building`: botão **Send Preview to Client** (define/usa `site_url` e muda para `preview`).
  - `preview`: botões **Move to Review** e **Mark Delivered**.
  - `review`: botão **Mark Delivered**.
- **Campos editáveis**:
  - `expected_delivery_date` (date picker).
  - `admin_notes` (textarea para notas internas).
  - Futuro: prioridade do projeto, tipo de plano/pacote.

### 3.2. Briefing & Strategy

- Resumo estruturado do `SiteOnboarding`:
  - Identidade do negócio (nome, nicho, cidade, serviço principal).
  - Objetivos do site.
  - Público alvo e regiões.
  - Páginas selecionadas.
  - Tom de voz, CTA, cores, referências, redes sociais.
  - Depoimentos e provas sociais.
- **Ações com IA**:
  - **Generate Briefing Document** – gera documento estratégico com IA (deliverable `briefing`).
  - **Generate Sitemap (AI)** – gera sitemap/arquitetura pro site (deliverable `sitemap`).
  - **Generate Home Copy Draft (AI)** – gera rascunho de textos da Home (deliverable `content_plan` com metadados).

### 3.3. Production / Deliverables

- Usa `SiteDeliverable` para armazenar artefatos:
  - `briefing`, `sitemap`, `content_plan`, `wireframe`, `code`.
- Cada deliverable:
  - `status`: `pending`, `generating`, `ready`, `approved`, `rejected`.
  - `content`: texto Markdown/JSON.
  - `metadata_json`: informações extras (ex: página alvo, se visível para cliente).
- Ações:
  - Marcar como `READY`, `APPROVED`, `REJECTED`.
  - Abrir conteúdo em modal (já implementado).

### 3.4. Comunicação

- Chat contínuo entre equipe e cliente.
- Upload de arquivos, links e mensagens categorizadas.
- Integração com status (ex: ao enviar preview ou solicitar revisão).

## 4. Papéis da IA no Fluxo

### 4.1. Strategic Briefing

- Task type: `site_briefing`.
- Entrada:
  - Dados de onboarding,
  - Notas internas,
  - Mensagens relevantes.
- Saída:
  - Documento estruturado com:
    - Visão geral do negócio,
    - Público-alvo,
    - Objetivos,
    - Proposta de valor,
    - Riscos e oportunidades.
- Armazenado em `SiteDeliverable(type=briefing, status=ready, is_visible_to_client=False)`.

### 4.2. Sitemap / Arquitetura

- Task type: `site_sitemap`.
- Entrada:
  - Páginas selecionadas,
  - Objetivos do site,
  - Nicho e serviços.
- Saída:
  - Lista de páginas e seções:
    - `home` → seções (hero, serviços, depoimentos, CTA final…)
    - `about` → história, equipe, valores…
    - `services` → lista de serviços com estrutura recomendada…
- Armazenado como `DeliverableType.SITEMAP`.

### 4.3. Draft de Conteúdo (Home Page)

- Task type: `site_home_copy`.
- Entrada:
  - Briefing estratégico e sitemap.
- Saída:
  - Rascunho de headings, subheadings, bullets, CTAs para a Home.
- Armazenado como `DeliverableType.CONTENT_PLAN` com `metadata_json.page = 'home'`.

### 4.4. SEO & CTAs (futuro)

- Task types:
  - `site_seo_meta`
  - `site_cta_variations`
- Gera:
  - `meta_title`, `meta_description`, keywords.
  - 3–5 variações de CTA com diferentes tons.

## 5. Endpoints Planejados (Backend)

### 5.1. Geração de Briefing (já implementado, evoluir para IA)

- `POST /api/site-orders/{order_id}/deliverables/briefing`
  - Carrega `SiteOrder` + `SiteOnboarding`.
  - Gera conteúdo (atualmente via template, futuro via `AIService`).
  - Cria `SiteDeliverable(type=briefing, status=ready)`.

### 5.2. Geração de Sitemap (AI)

- `POST /api/site-orders/{order_id}/ai/plan-sitemap`
  - Usa `AIService.generate(task_type="site_sitemap", ...)`.
  - Salva resultado em `SiteDeliverable(type=sitemap, status=ready)`.

### 5.3. Geração de Home Copy (AI)

- `POST /api/site-orders/{order_id}/ai/home-copy`
  - Usa `AIService.generate(task_type="site_home_copy", ...)`.
  - Salva em `SiteDeliverable(type=content_plan, metadata_json={"page": "home"})`.

## 6. Integração Frontend (CRM)

- Rotas proxy Next:
  - `POST /api/site-orders/[id]/deliverables/briefing`
  - `POST /api/site-orders/[id]/ai/plan-sitemap`
  - `POST /api/site-orders/[id]/ai/home-copy`
- Botões no modal (aba Briefing & Strategy):
  - Generate Briefing Document (AI).
  - Generate Sitemap (AI).
  - Generate Home Copy (AI).
- Após cada geração:
  - Mostrar toast de sucesso.
  - Atualizar lista de deliverables (`loadOrders()`).

## 7. Princípios

- IA **não gera código nem toma decisão de layout**.
- Tudo que a IA gera é sempre:
  - Texto / estrutura,
  - Passa por revisão humana,
  - Fica registrado como deliverable.
- O cliente vê apenas:
  - Status, preview, comunicação,
  - Alguns deliverables marcados explicitamente como visíveis.

