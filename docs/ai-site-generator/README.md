# AI Site Generator - Documentação Técnica

## 📋 Índice

1. [README.md](./README.md) - Este arquivo (visão geral)
2. [ARCHITECTURE.md](./ARCHITECTURE.md) - Arquitetura técnica completa
3. [FEATURES.md](./FEATURES.md) - Especificação de features
4. [ROADMAP.md](./ROADMAP.md) - Roadmap de desenvolvimento
5. [INTEGRATIONS.md](./INTEGRATIONS.md) - Integrações externas
6. [DATA_MODEL.md](./DATA_MODEL.md) - Modelo de dados
7. [API_SPEC.md](./API_SPEC.md) - Especificação de APIs
8. [SITE_SPEC_SCHEMA.md](./SITE_SPEC_SCHEMA.md) - Schema do site_spec.json
9. [DEVELOPMENT_RULES.md](./DEVELOPMENT_RULES.md) - Regras de desenvolvimento

---

## 🎯 Visão Geral

**AI Site Generator** é um sistema automatizado que permite gerar sites profissionais através de IA, integrado ao fluxo de checkout → onboarding → entrega da Innexar.

### Objetivo Principal

Após o cliente completar o onboarding:
1. IA cria projeto do cliente (estrutura + spec)
2. IA cria documentação inicial (brief, sitemap, conteúdo)
3. IA gera primeira versão do site (repo Git + build + preview)
4. Sistema mantém ciclo de revisão (IA + humano) até entregar

### Fluxo de Alto Nível

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│  Checkout   │───▶│  Onboarding  │───▶│   Pipeline  │───▶│   Entrega   │
│   (Stripe)  │    │  (Coleta)    │    │   (IA+Build)│    │  (Preview)  │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
                          │                    │
                          ▼                    ▼
                   ┌─────────────┐      ┌─────────────┐
                   │   Storage   │      │   GitHub    │
                   │   (R2/S3)   │      │   (Repos)   │
                   └─────────────┘      └─────────────┘
```

### Princípios de Design

1. **IA não executa, apenas produz artefatos**
   - JSON schemas validados
   - Patches/diffs de código
   - Documentação estruturada

2. **Builds são obrigatórios**
   - Sem build OK → sem deploy
   - Retry limitado (2-3 tentativas)
   - Fallback para humano

3. **Preview antes de produção**
   - Subdomínio temporário
   - Aprovação cliente + humano
   - Histórico de revisões

---

## 🏗️ Stack Tecnológico

| Componente | Tecnologia | Propósito |
|------------|------------|-----------|
| Backend API | FastAPI (Python) | Orquestração, estado, auth |
| Fila/Workers | Celery + Redis | Jobs assíncronos |
| Database | PostgreSQL | Estado persistente |
| Cache | Redis | Fila + cache |
| Storage | Cloudflare R2 | Assets (logo, imagens) |
| Git | GitHub API | Repositórios e commits |
| Deploy | Cloudflare Pages | Preview e produção |
| DNS | Cloudflare | Subdomínios dinâmicos |
| IA Conteúdo | Claude/GPT-4 | Geração de copy |
| IA Código | Claude/Codex | Geração de patches |

---

## 📁 Estrutura da Documentação

```
docs/ai-site-generator/
├── README.md              # Visão geral (este arquivo)
├── ARCHITECTURE.md        # Arquitetura detalhada
├── FEATURES.md            # Features e specs
├── ROADMAP.md             # Fases de desenvolvimento
├── INTEGRATIONS.md        # Integrações externas
├── DATA_MODEL.md          # Tabelas e relações
├── API_SPEC.md            # Endpoints da API
└── SITE_SPEC_SCHEMA.md    # Schema JSON do site
```

---

## 🚀 Status do Projeto

| Fase | Status | Descrição |
|------|--------|-----------|
| Fase 1 | 🔴 Não iniciada | Configurações e integrações |
| Fase 2 | 🔴 Não iniciada | Pipeline básico |
| Fase 3 | 🔴 Não iniciada | Geração de conteúdo |
| Fase 4 | 🔴 Não iniciada | Geração de código |
| Fase 5 | 🔴 Não iniciada | Deploy e preview |
| Fase 6 | 🔴 Não iniciada | Ciclo de revisão |

---

## 📞 Responsáveis

- **Arquiteto**: Vinicius Vasques
- **Desenvolvimento**: Equipe Innexar
- **IA Assistant**: Helena

---

*Última atualização: Janeiro 2026*
