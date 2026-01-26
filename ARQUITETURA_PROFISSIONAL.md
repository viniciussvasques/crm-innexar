# Arquitetura Profissional - Sistema de Geração de Sites

## 1. Visão Geral

O sistema gera sites Next.js automaticamente usando IA, seguindo um pipeline de 3 fases:
1. **Phase 1: Strategic Briefing** - IA analisa negócio e cria briefing
2. **Phase 2: Code Generation** - IA gera código Next.js completo
3. **Phase 3: Review** - Site pronto para revisão

## 2. Onde os Sites São Guardados

### Estrutura de Diretórios

```
Host (Docker):
./data/generated_sites/
  └── project_{order_id}/
      ├── app/
      │   ├── page.tsx
      │   ├── layout.tsx
      │   └── ...
      ├── components/
      ├── public/
      └── package.json

Container:
/app/generated_sites/
  └── project_{order_id}/
      └── (mesma estrutura)
```

### Volume Compartilhado

- **Host**: `./data/generated_sites` (relativo ao docker-compose.yml)
- **Container Backend**: `/app/generated_sites` (montado via volume)
- **Container Worker**: `/app/generated_sites` (montado via volume)

**Garantia**: Ambos containers acessam o mesmo diretório físico.

### Código de Acesso

**Backend (API de Files)**:
```python
# app/api/site_files.py
SITES_BASE_DIR = "/app/generated_sites"  # Absoluto
project_dir = SITES_BASE_DIR / f"project_{project_id}"
```

**Worker (Geração)**:
```python
# app/services/site_generator_service.py
base_dir = os.getenv("SITES_BASE_DIR", "/app/generated_sites")
target_dir = os.path.join(base_dir, f"project_{order_id}")
```

## 3. Fluxo de Geração

### 3.1 Trigger de Geração

```
Frontend → POST /api/site-orders/{id}/build
  ↓
Backend → Celery Task (generate_site_task)
  ↓
Worker → SiteGeneratorService.generate_site()
```

### 3.2 Pipeline de Geração

```
1. VALIDATE
   ├── Verifica onboarding completo
   ├── Verifica status (não regenera se REVIEW/COMPLETED)
   └── Carrega dados do pedido

2. PHASE_1: Strategic Briefing
   ├── Verifica se já existe briefing
   ├── Se não existe: Gera via IA
   └── Salva em SiteDeliverable (type=BRIEFING)

3. PHASE_2: Code Generation
   ├── Constrói prompt com briefing + onboarding
   ├── Chama IA para gerar código
   ├── Parse JSON da resposta
   └── Escreve arquivos em /app/generated_sites/project_{id}/

4. FINALIZE
   ├── Atualiza status para REVIEW
   ├── Define site_url
   └── Loga sucesso
```

### 3.3 Status Automático

O status é atualizado automaticamente durante a geração:

- `BUILDING` → Quando build é disparado
- `GENERATING` → Durante geração
- `REVIEW` → Quando arquivos são escritos com sucesso
- `COMPLETED` → Manualmente pelo admin

## 4. Sistema de Templates (Proposta)

### 4.1 Por Que Templates?

**Problema Atual**: IA gera tudo do zero, consumindo muitos tokens.

**Solução**: Usar templates base e IA apenas customiza.

### 4.2 Estrutura de Templates

```
backend/templates/
├── landing-page/
│   ├── base/
│   │   ├── app/
│   │   ├── components/
│   │   └── package.json
│   ├── variants/
│   │   ├── saas.json
│   │   ├── ecommerce.json
│   │   └── portfolio.json
│   └── prompts/
│       └── customization.md
│
├── saas-platform/
│   └── (estrutura similar)
│
└── portfolio/
    └── (estrutura similar)
```

### 4.3 Fluxo com Templates

```
1. Selecionar Template Base
   ├── Baseado em niche/onboarding
   └── Copia estrutura base

2. Customização via IA
   ├── Aplica variante (cores, layout)
   ├── Customiza conteúdo (textos, imagens)
   └── Ajusta componentes específicos

3. Geração Final
   └── Template + Customizações = Site Final
```

### 4.4 Economia de Tokens

**Sem Template**: ~50k tokens (gerar tudo)
**Com Template**: ~10k tokens (apenas customização)

**Economia**: ~80% de tokens

## 5. Endpoints Críticos

### 5.1 Status (CORRIGIDO)

```python
PATCH /api/site-orders/{id}/status
Body: { "status": "REVIEW", "admin_notes": "...", "site_url": "..." }
```

**Uso**: Frontend atualiza status manualmente ou sistema atualiza automaticamente.

### 5.2 Files

```python
GET /api/projects/{id}/files          # Lista arquivos
GET /api/projects/{id}/files/content  # Lê arquivo
POST /api/projects/{id}/files/content # Salva arquivo
```

**Uso**: IDE lista e edita arquivos gerados.

### 5.3 Preview

```python
GET /api/projects/{id}/preview?path=index.html
```

**Uso**: Preview do site no IDE.

## 6. Garantias de Funcionamento

### 6.1 Volume Compartilhado

✅ **Garantido**: `docker-compose.yml` monta volume em ambos containers

### 6.2 Caminhos Absolutos

✅ **Garantido**: Todos usam `/app/generated_sites` (absoluto)

### 6.3 Status Automático

✅ **Garantido**: `SiteGeneratorService` atualiza status automaticamente

### 6.4 Deliverables

✅ **Garantido**: `selectinload(SiteOrder.deliverables)` na listagem

### 6.5 Event Loop

✅ **Garantido**: Engine isolado por execução, sem conflitos

## 7. Próximos Passos (Implementação)

### 7.1 Sistema de Templates

1. Criar estrutura de templates
2. Implementar seletor de template baseado em niche
3. Modificar `SiteGeneratorService` para usar templates
4. Reduzir prompt da IA para apenas customização

### 7.2 Melhorias de Status

1. WebSocket para atualização em tempo real
2. Polling automático no frontend
3. Notificações quando status muda

### 7.3 Preview Funcional

1. Servir arquivos estáticos via nginx
2. Ou usar Cloudflare Pages para deploy automático
3. Configurar preview.innexar.com

## 8. Checklist de Funcionamento

- [x] Volume compartilhado configurado
- [x] Caminhos absolutos garantidos
- [x] Endpoint de status criado
- [x] Deliverables carregados
- [x] Event loop isolado
- [ ] Templates implementados
- [ ] Preview funcional
- [ ] Status em tempo real

## 9. Documentação de Código

### 9.1 Onde Arquivos São Salvos

**Função**: `SiteGeneratorService._get_target_dir(order_id)`
**Localização**: `backend/app/services/site_generator_service.py:86`
**Retorna**: `/app/generated_sites/project_{order_id}`

### 9.2 Como Arquivos São Acessados

**API**: `GET /api/projects/{id}/files`
**Handler**: `site_files.list_files()`
**Localização**: `backend/app/api/site_files.py:77`

### 9.3 Como Status É Atualizado

**Automático**: `SiteGeneratorService.generate_site()` atualiza para REVIEW
**Manual**: `PATCH /api/site-orders/{id}/status`

## 10. Conclusão

O sistema está **arquiteturalmente correto**. As correções aplicadas garantem:

1. ✅ Arquivos salvos em local compartilhado
2. ✅ Acesso consistente via API
3. ✅ Status atualizado automaticamente
4. ✅ Deliverables exibidos corretamente
5. ✅ Sem conflitos de event loop

**Próximo passo**: Implementar sistema de templates para economizar tokens.
