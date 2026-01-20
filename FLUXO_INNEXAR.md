# 🔄 Fluxo de Trabalho Innexar - CRM Adaptado

## 🎯 Modelo de Negócio Innexar

A Innexar é uma **full-stack digital studio** que desenvolve:
- **Marketing Sites** - Sites de marketing e conversão
- **SaaS Platforms** - Plataformas SaaS (Innexar ERP, StructurOne)
- **Enterprise Software** - Software empresarial customizado
- **Consultoria** - Estratégia, design, desenvolvimento

## 📊 Fluxo de Trabalho Implementado

### 1. Captação de Leads (Vendedor)
```
Lead do Site → API Externa → Contato Criado → Atribuído ao Vendedor
```

### 2. Qualificação e Proposta
```
Contato → Oportunidade → Proposta → Aguardando Aprovação
```

### 3. Projeto Aprovado
```
Cliente Aprova → Projeto Criado → Status: APROVADO
```

### 4. Envio para Equipe Técnica
```
Vendedor → Envia Projeto → Atribui Técnico → Status: EM_DESENVOLVIMENTO
```

### 5. Desenvolvimento
```
Técnico → Trabalha no Projeto → Atualiza Status → Entrega
```

## 🗄️ Estrutura de Dados

### Projeto (Project)
- **Tipos**: Marketing Site, SaaS Platform, Enterprise Software, Custom Development, Consulting
- **Status**: Lead → Qualificação → Proposta → Aprovado → Em Desenvolvimento → Em Revisão → Concluído
- **Atribuições**: Vendedor (owner) + Técnico (technical_owner)

### Relacionamentos
- Contact → Projects (1:N)
- Opportunity → Projects (1:N) - Projeto pode vir de oportunidade
- User (Vendedor) → Projects (1:N) - Projetos do vendedor
- User (Técnico) → Projects (1:N) - Projetos atribuídos ao técnico
- Project → Activities (1:N) - Atividades relacionadas ao projeto

## 🔌 APIs Externas

### 1. Web-to-Lead API
**Endpoint**: `POST /api/external/web-to-lead`
**Autenticação**: Header `X-API-Token`

**Uso**: Formulários do site Innexar podem enviar leads diretamente para o CRM

**Exemplo**:
```bash
curl -X POST https://api.sales.innexar.app/api/external/web-to-lead \
  -H "Content-Type: application/json" \
  -H "X-API-Token: seu-token-aqui" \
  -d '{
    "name": "João Silva",
    "email": "joao@example.com",
    "phone": "+5511999999999",
    "company": "Empresa XYZ",
    "message": "Preciso de um site",
    "source": "website",
    "project_type": "marketing_site"
  }'
```

**O que faz**:
1. Cria contato automaticamente
2. Atribui ao vendedor disponível
3. Opcionalmente cria projeto se `project_type` for fornecido
4. Deduplica por email (atualiza se já existir)

### 2. API de Projetos
**Endpoints**:
- `GET /api/projects` - Lista projetos
- `GET /api/projects/{id}` - Detalhes do projeto
- `POST /api/projects` - Criar projeto
- `PATCH /api/projects/{id}` - Atualizar projeto
- `POST /api/projects/{id}/send-to-technical` - Enviar para técnico
- `DELETE /api/projects/{id}` - Deletar (apenas admin)

## 👥 Roles e Permissões

### Admin
- Ver todos os projetos
- Criar/editar/deletar projetos
- Atribuir técnicos
- Ver todos os vendedores e técnicos

### Vendedor
- Ver apenas seus próprios projetos
- Criar projetos
- Enviar projetos para técnicos
- Atualizar status até "Aprovado"

### Técnico
- Ver apenas projetos atribuídos a ele
- Atualizar status técnico
- Adicionar notas técnicas
- Atualizar URLs (repositório, deploy)

## 🚀 Próximos Passos

### Frontend
1. Criar página de Projetos
2. Interface para vendedor criar projeto
3. Interface para técnico gerenciar projetos
4. Pipeline visual com estágios Innexar

### Integrações
1. Webhook para notificações
2. Integração com repositórios Git
3. Sincronização com sistemas internos

### Melhorias
1. Templates de projeto por tipo
2. Estimativas automáticas
3. Relatórios de projetos
4. Dashboard de projetos

