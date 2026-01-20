# 🏗️ Estrutura CRM Innexar - Adaptado ao Modelo de Negócio

## 👥 Roles (Papéis)

### Admin
- Acesso total ao sistema
- Gerencia usuários
- Vê todos os projetos

### Vendedor
- Capta leads e clientes
- Cria oportunidades e projetos
- Envia projetos para planejamento
- Acompanha seus projetos

### Planejamento
- Recebe projetos aprovados
- Planeja e estrutura projetos
- Envia para desenvolvimento
- Atualiza requisitos e especificações

### Dev (Desenvolvimento)
- Recebe projetos do planejamento
- Desenvolve projetos
- Atualiza status e URLs
- Entrega projetos

## 🔄 Fluxo Completo

```
1. Lead do Site
   ↓
2. Vendedor Qualifica
   ↓
3. Cria Oportunidade/Proposta
   ↓
4. Cliente Aprova
   ↓
5. Projeto Criado (Status: APROVADO)
   ↓
6. Vendedor → Envia para Planejamento
   ↓
7. Planejamento → Planeja e Estrutura
   ↓
8. Planejamento → Envia para Dev
   ↓
9. Dev → Desenvolve (Status: EM_DESENVOLVIMENTO)
   ↓
10. Dev → Entrega (Status: CONCLUIDO)
```

## 📊 Modelo de Projeto

### Campos Principais
- **owner_id**: Vendedor responsável
- **planning_owner_id**: Responsável planejamento
- **dev_owner_id**: Responsável desenvolvimento
- **sent_to_planning_at**: Data envio para planejamento
- **sent_to_dev_at**: Data envio para desenvolvimento

### Status do Projeto
1. **LEAD** - Lead captado
2. **QUALIFICACAO** - Vendedor qualificando
3. **PROPOSTA** - Proposta criada
4. **APROVADO** - Cliente aprovou, pronto para planejamento
5. **EM_DESENVOLVIMENTO** - Equipe dev trabalhando
6. **EM_REVISAO** - Em revisão/ajustes
7. **CONCLUIDO** - Projeto entregue
8. **CANCELADO** - Projeto cancelado

## 🔌 APIs

### Web-to-Lead (Externa)
`POST /api/external/web-to-lead`
- Recebe leads do site
- Cria contato automaticamente
- Opcionalmente cria projeto

### Projetos
- `GET /api/projects` - Lista projetos
- `POST /api/projects` - Criar projeto
- `PATCH /api/projects/{id}` - Atualizar
- `POST /api/projects/{id}/send-to-planning` - Enviar para planejamento
- `POST /api/projects/{id}/send-to-dev` - Enviar para desenvolvimento

## 🎯 Próximos Passos Frontend

1. Página de Projetos
2. Formulário criar projeto
3. Interface planejamento
4. Interface desenvolvimento
5. Pipeline visual

