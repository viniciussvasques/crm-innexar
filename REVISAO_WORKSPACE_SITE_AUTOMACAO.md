# Revisão profissional do Workspace (CRM) + Automação de geração de sites (SLA 5 dias)

## 1) Objetivo
Transformar o CRM em um **workspace operacional** onde o site se vende sozinho (checkout + onboarding no site principal), e o CRM assume:
- Orquestração da geração do site por etapas.
- Portal do cliente com status, preview e revisões.
- Revisão humana de código **apenas quando necessário**.
- Entrega em **até 5 dias**.

## 2) Visão geral do fluxo ponta‑a‑ponta
1. **Checkout + Onboarding** no site principal.
2. **CRM/Workspace** recebe o onboarding e cria o projeto.
3. **Pipeline automático** gera spec, docs, código, build e preview.
4. **Portal do cliente** libera preview e recebe revisões.
5. **Revisão humana** apenas se falhar build ou houver pedido específico.
6. **Aprovação final** e entrega.

## 3) Pipeline recomendado (SLA 5 dias)
**Dia 0–1: Intake + Spec**
- Validação de dados e assets.
- Criação do `site_spec.json` e checklist de pendências.

**Dia 1–2: Documentação**
- Brief + sitemap + conteúdo base.
- Artefatos publicados no portal.

**Dia 2–3: Código**
- Provisiona repo/branch.
- IA gera patch/diff com base no spec.
- Build obrigatório + relatório.

**Dia 3–4: Preview**
- Deploy automático.
- Subdomínio de preview.
- Portal exibe preview.

**Dia 4–5: Revisão e entrega**
- Revisões do cliente (se houver) viram patches.
- Revisão humana só se necessário.
- Handoff final.

## 4) Configurações de infraestrutura (centralizar no Workspace)
### 4.1 Cloudflare (DNS + Deploy + CDN)
**Configurações essenciais**
- **Zone ID / API Token** (permissões de DNS + Pages).
- **Subdomínio de preview** (ex.: `clienteX.seudominio.com`).
- **Configuração de SSL** (Full/Strict).

**Fluxo**
1. Deploy automático gera preview URL.
2. Workspace registra preview URL no projeto.
3. DNS é criado/atualizado para apontar preview.

### 4.2 Git (GitHub ou GitLab)
**Configurações essenciais**
- **Token com permissão de repo**.
- **Template base** (repo modelo).
- **Branch padrão por cliente**.

**Fluxo**
1. Provisionamento de repo (ou branch) a partir do template.
2. Aplicação de patches gerados pela IA.
3. Build no runner e commit automático.

### 4.3 Deploy (Cloudflare Pages / Vercel / Netlify)
**Configurações essenciais**
- **Provider padrão**.
- **Project ID / Site ID**.
- **Build command** + **Output directory**.
- **Variáveis de ambiente**.

### 4.4 Runner seguro (build/test)
- Build isolado (container por job).
- Logs curtos publicados no workspace.
- Retentativas limitadas.

## 5) Configurações de IA (profissional e centralizado)
### 5.1 Tipos de IA no sistema
1. **IA de Conversação** (já existente)
   - Atendimento e suporte no portal.
2. **IA de Geração de Site** (nova)
   - Cria spec, docs, layout e patches de código.

### 5.2 Campos essenciais na configuração de IA (Admin)
- **Provider** (OpenAI / Anthropic / Local).
- **Modelo** (ex.: GPT‑4.1 / Claude / Llama local).
- **Budget mensal**.
- **Max tokens**.
- **Temperatura**.
- **Retries por etapa**.
- **Timeout por etapa**.
- **Allowlist de arquivos editáveis**.
- **Schema de saída obrigatório**.

### 5.3 Separação clara por módulos
- **IA de conversação**: prompt e regras próprias.
- **IA de geração**: prompt + schema + validação.

## 6) Portal do cliente (no CRM)
Funcionalidades obrigatórias:
- Status do pipeline por etapa.
- Preview link.
- Solicitação de revisão.
- Aprovação final.

## 7) Eventos para integração interna
- `project.created`
- `spec.created`
- `docs.generated`
- `repo.provisioned`
- `build.succeeded / build.failed`
- `deploy.ready`
- `client.requested_revision`
- `human.approved`

## 8) Segurança e governança
- IA só gera **artefatos**, não executa ações.
- Build obrigatório antes de deploy.
- Retentativas limitadas (2–3).
- Se falhar, vira tarefa humana.

## 9) Plano de execução (passos concretos)
1. **Configurar integrações** no workspace (Cloudflare, Git, Deploy) com tokens, IDs e templates.
2. **Cadastrar providers de IA** (Conversação e Geração) e schemas obrigatórios.
3. **Criar endpoints mínimos** no backend para gerar, revisar e aprovar.
4. **Criar o dashboard do projeto** com pipeline, artefatos e preview.
5. **Habilitar runner isolado** para builds e testes.
6. **Ativar deploy automático** + registro de preview no portal.

## 10) Checklist de configuração (para execução rápida)
### Infra
- [ ] Token Cloudflare com DNS + Pages
- [ ] Zone ID
- [ ] Domínio de preview configurado
- [ ] Token Git (repo write)
- [ ] Repo template definido
- [ ] Provider de deploy definido (Pages/Vercel/Netlify)
- [ ] Build command e output dir definidos

### IA
- [ ] Provider da IA de conversação
- [ ] Provider da IA de geração
- [ ] Prompts por etapa
- [ ] Schemas de saída
- [ ] Allowlist de arquivos
- [ ] Retry/timeout definidos
