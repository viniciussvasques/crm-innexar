# Features - AI Site Generator

## Índice de Features

| ID | Feature | Prioridade | Fase |
|----|---------|------------|------|
| F01 | Configurações de Integrações | Alta | 1 |
| F02 | Pipeline de Geração | Alta | 2 |
| F03 | Geração de Conteúdo (IA) | Alta | 3 |
| F04 | Geração de Código (IA) | Alta | 4 |
| F05 | Deploy e Preview | Alta | 5 |
| F06 | Ciclo de Revisão | Média | 6 |
| F07 | Templates Customizáveis | Média | 7 |
| F08 | Analytics e Métricas | Baixa | 8 |

---

## F01 - Configurações de Integrações

### Descrição
Página de configurações no CRM para gerenciar todas as integrações externas necessárias para o AI Site Generator.

### User Stories
- Como admin, quero configurar credenciais do GitHub para criar repositórios
- Como admin, quero configurar Cloudflare para deploy e DNS
- Como admin, quero configurar modelos de IA diferentes para cada tipo de tarefa
- Como admin, quero testar cada integração antes de ativar

### Integrações Necessárias

#### 1. GitHub
```yaml
config:
  access_token: "ghp_xxx..."
  organization: "innexar-clients"
  template_repos:
    landing: "innexar-clients/template-landing"
    saas: "innexar-clients/template-saas"
    portfolio: "innexar-clients/template-portfolio"
```

#### 2. Cloudflare
```yaml
config:
  api_token: "xxx"
  account_id: "xxx"
  zone_id: "xxx"  # Para DNS
  pages_project: "innexar-sites"
  r2_bucket: "innexar-assets"
  preview_domain: "preview.innexar.app"
```

#### 3. AI Models (Criação de Sites)
```yaml
config:
  content_generation:
    provider: "anthropic"
    model: "claude-3-5-sonnet-20241022"
    api_key: "sk-ant-xxx"
    max_tokens: 4000
  code_generation:
    provider: "anthropic"
    model: "claude-3-5-sonnet-20241022"
    api_key: "sk-ant-xxx"
    max_tokens: 8000
  analysis:
    provider: "openai"
    model: "gpt-4o"
    api_key: "sk-xxx"
```

#### 4. Storage (R2/S3)
```yaml
config:
  provider: "cloudflare_r2"
  bucket: "innexar-assets"
  access_key_id: "xxx"
  secret_access_key: "xxx"
  endpoint: "https://xxx.r2.cloudflarestorage.com"
  public_url: "https://assets.innexar.app"
```

### Mockup UI

```
┌─────────────────────────────────────────────────────────────┐
│ Settings > Integrations                                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 🐙 GitHub                                    ✅ Connected ││
│  │   Organization: innexar-clients                          ││
│  │   Templates: 3 configurados                              ││
│  │   [Test Connection] [Edit]                               ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ ☁️ Cloudflare                               ✅ Connected ││
│  │   Account: Innexar                                       ││
│  │   Pages Project: innexar-sites                           ││
│  │   [Test Connection] [Edit]                               ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 🤖 AI Models (Site Generator)              ✅ Configured ││
│  │   Content: Claude 3.5 Sonnet                             ││
│  │   Code: Claude 3.5 Sonnet                                ││
│  │   [Test Models] [Edit]                                   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 📦 Storage (R2)                            ✅ Connected ││
│  │   Bucket: innexar-assets                                 ││
│  │   Usage: 2.3 GB / 10 GB                                  ││
│  │   [Test Connection] [Edit]                               ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Critérios de Aceite
- [ ] Página de integrações acessível em Settings
- [ ] Formulários de configuração para cada integração
- [ ] Botão "Test Connection" funcional
- [ ] Indicador visual de status (connected/error)
- [ ] Logs de teste visíveis
- [ ] Secrets armazenados de forma segura (encrypted)

---

## F02 - Pipeline de Geração

### Descrição
Sistema de pipeline que orquestra todas as etapas de geração de um site.

### Etapas do Pipeline

```
ETAPA A: Ingestão e Normalização
├── A1. Validate Onboarding
├── A2. Download Assets
└── A3. Create Site Spec

ETAPA B: Documentação (IA)
├── B1. Generate Brief
├── B2. Generate Sitemap
└── B3. Generate Content

ETAPA C: Projeto
├── C1. Provision Repository
└── C2. Setup Structure

ETAPA D: Geração
├── D1. Generate Layout Plan
├── D2. Generate Code Patch
├── D3. Apply Patch
└── D4. Build and Test

ETAPA E: Deploy
├── E1. Deploy Preview
└── E2. Provision Subdomain

ETAPA F: Revisão
├── F1. Human Review
├── F2. Client Review
└── F3. Approve and Handoff
```

### Estados de Step

| Estado | Descrição |
|--------|-----------|
| `queued` | Aguardando execução |
| `running` | Em execução |
| `success` | Concluído com sucesso |
| `failed` | Falhou (pode ter retry) |
| `skipped` | Pulado (dependência falhou) |
| `manual` | Requer ação humana |

### Visualização no Portal

```
┌─────────────────────────────────────────────────────────────┐
│ Projeto: Dhv Group Service                                   │
│ Status: Em Desenvolvimento                                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ● Pagamento ──● Onboarding ──● Documentação ──○ Código     │
│       ✓             ✓              ✓             ◐          │
│                                                              │
│  ──○ Build ──○ Preview ──○ Revisão ──○ Entrega              │
│       ○          ○           ○          ○                   │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ Etapa Atual: Gerando código do site...                       │
│ Tempo estimado: ~5 minutos                                   │
│                                                              │
│ [Ver Detalhes] [Logs] [Pausar]                              │
└─────────────────────────────────────────────────────────────┘
```

---

## F03 - Geração de Conteúdo (IA)

### Descrição
Uso de IA para gerar todo conteúdo textual do site.

### Artefatos Gerados

#### 1. Brief (brief.md)
- Objetivos do site
- Público-alvo
- Tom de voz
- Proposta de valor
- Diferenciais

#### 2. Sitemap (sitemap.json)
```json
{
  "pages": [
    {
      "slug": "home",
      "title": "Home",
      "sections": ["hero", "services", "about", "testimonials", "cta"]
    },
    {
      "slug": "about",
      "title": "Sobre Nós",
      "sections": ["hero", "story", "team", "values"]
    }
  ]
}
```

#### 3. Content (content.json)
```json
{
  "home": {
    "hero": {
      "headline": "Transformamos ideias em soluções digitais",
      "subheadline": "Desenvolvemos sites e aplicações que...",
      "cta": "Solicite um Orçamento"
    },
    "services": {
      "title": "Nossos Serviços",
      "items": [...]
    }
  }
}
```

---

## F04 - Geração de Código (IA)

### Descrição
Uso de IA para gerar e modificar código do site.

### Fluxo

1. **Layout Plan**: IA analisa template e decide quais componentes usar
2. **Code Patch**: IA gera diffs para preencher template com conteúdo
3. **Apply**: Backend aplica patches no repositório
4. **Validate**: Build runner valida que código compila

### Formato de Patch (Unified Diff)
```diff
--- a/src/components/Hero.tsx
+++ b/src/components/Hero.tsx
@@ -5,7 +5,7 @@
 export function Hero() {
   return (
     <section className="hero">
-      <h1>Placeholder Headline</h1>
+      <h1>Transformamos ideias em soluções digitais</h1>
       <p>Subheadline here</p>
     </section>
   )
 }
```

### Allowlist de Arquivos

A IA só pode modificar arquivos da allowlist:
```yaml
editable_files:
  - "src/content/**/*.json"
  - "src/components/sections/**/*.tsx"
  - "src/app/page.tsx"
  - "public/images/**/*"
  - "tailwind.config.js" # colors only

readonly_files:
  - "src/lib/**/*"
  - "package.json"
  - "next.config.js"
```

---

## F05 - Deploy e Preview

### Descrição
Deploy automático para preview e produção.

### Fluxo de Deploy

```
1. Push para branch preview-{project_id}
2. Cloudflare Pages detecta push
3. Build automático
4. Preview URL gerada
5. DNS record criado para subdomínio
6. Cliente notificado
```

### Subdomínios

- Preview: `{slug}.preview.innexar.app`
- Produção: Cliente configura domínio próprio

---

## F06 - Ciclo de Revisão

### Descrição
Fluxo de revisão humana e do cliente antes da entrega final.

### Tipos de Revisão

1. **Human Review** (interno)
   - Checklist de qualidade
   - Copy editing
   - Consistência visual
   - Links funcionando

2. **Client Review** (portal)
   - Cliente visualiza preview
   - Cliente envia alterações
   - IA processa e aplica

### Estados de Revisão

| Estado | Descrição |
|--------|-----------|
| `pending_review` | Aguardando revisão |
| `changes_requested` | Alterações solicitadas |
| `in_progress` | Alterações sendo aplicadas |
| `approved` | Aprovado para entrega |

---

## F07 - Templates Customizáveis

### Descrição
Catálogo de templates base que podem ser customizados.

### Templates Disponíveis

| Template | Tipo | Páginas |
|----------|------|---------|
| Landing Page | Marketing | 1 página |
| Business | Institucional | 5-7 páginas |
| SaaS Platform | Produto | 8-10 páginas |
| Portfolio | Criativo | 4-6 páginas |
| E-commerce | Loja | 10+ páginas |

### Estrutura de Template

```
template-landing/
├── src/
│   ├── components/
│   │   ├── sections/          # Seções editáveis
│   │   │   ├── Hero.tsx
│   │   │   ├── Features.tsx
│   │   │   └── CTA.tsx
│   │   └── ui/                # Componentes base (readonly)
│   ├── content/
│   │   └── site.json          # Conteúdo editável
│   └── styles/
│       └── theme.json         # Cores/fontes editáveis
├── public/
│   └── images/
└── template.config.yaml       # Configuração do template
```

---

## F08 - Analytics e Métricas

### Descrição
Dashboard com métricas de uso do sistema.

### Métricas

- Projetos gerados por período
- Tempo médio por etapa
- Taxa de sucesso/falha
- Custo de IA por projeto
- Revisões por projeto
- Tempo total até entrega

---

*Última atualização: Janeiro 2026*
