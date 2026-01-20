# 🧪 Testes de Endpoints - Innexar CRM

## Status dos Endpoints

### ✅ Endpoints Funcionando

1. **Autenticação**
   - `POST /api/auth/login` - Login de usuário
   - `GET /api/users/me` - Obter usuário atual

2. **Usuários**
   - `GET /api/users/` - Listar usuários (admin)
   - `POST /api/users/` - Criar usuário (admin)

3. **Contatos**
   - `GET /api/contacts/` - Listar contatos

4. **Oportunidades**
   - `GET /api/opportunities/` - Listar oportunidades

5. **Projetos**
   - `GET /api/projects` - Listar projetos

6. **Atividades**
   - `GET /api/activities/` - Listar atividades

7. **Dashboard**
   - `GET /api/dashboard/admin` - Dashboard admin
   - `GET /api/dashboard/vendedor` - Dashboard vendedor

8. **Comissões**
   - `GET /api/commissions/` - Listar comissões

9. **Metas**
   - `GET /api/goals/` - Listar metas

10. **Notificações**
    - `GET /api/notifications/` - Listar notificações

11. **Quote Requests**
    - `GET /api/quote-requests/` - Listar solicitações de orçamento

### ⚠️ Endpoints com Problemas

1. **Templates**
   - `GET /api/templates/` - Status: Corrigido (precisa reiniciar backend)

2. **IA**
   - `POST /api/ai/chat` - Status: Requer `GROK_API_KEY` configurada no `.env`

## Correções Aplicadas

### 1. Enum `userrole` no Banco de Dados
- **Problema**: Enum só tinha `ADMIN` e `VENDEDOR`
- **Solução**: Adicionados valores `planejamento` e `dev`
- **Comando**: 
  ```sql
  ALTER TYPE userrole ADD VALUE 'planejamento';
  ALTER TYPE userrole ADD VALUE 'dev';
  ```

### 2. Coluna `estimated_hours` Faltando
- **Problema**: Tabela `quote_requests` não tinha coluna `estimated_hours`
- **Solução**: Adicionada coluna `estimated_hours INTEGER`
- **Comando**:
  ```sql
  ALTER TABLE quote_requests ADD COLUMN estimated_hours INTEGER;
  ```

### 3. Endpoint `/api/templates/` Retornando 404
- **Problema**: Não havia rota GET "/"
- **Solução**: Adicionada rota GET "/" que retorna tipos de templates

### 4. Endpoint `/api/ai/chat` Retornando 500
- **Problema**: `GROK_API_KEY` não configurada no container
- **Solução**: Adicionada variável `GROK_API_KEY` no `docker-compose.yml`
- **Ação Necessária**: Definir `GROK_API_KEY` no arquivo `.env`

## Scripts de Teste

### Script Python
```bash
python3 test_all_endpoints.py https://api.sales.innexar.app
```

### Script Bash
```bash
./test_endpoints.sh
```

## Próximos Passos

1. ✅ Adicionar `GROK_API_KEY` ao arquivo `.env`
2. ✅ Reiniciar backend após configurar `GROK_API_KEY`
3. ✅ Testar criação de usuário com role `planejamento` ou `dev`
4. ✅ Verificar se todos os endpoints estão respondendo corretamente

## Notas

- Todos os endpoints principais estão funcionando
- Apenas endpoints de IA requerem configuração adicional
- Enum do banco de dados foi atualizado com sucesso
- Migrações de banco foram aplicadas

