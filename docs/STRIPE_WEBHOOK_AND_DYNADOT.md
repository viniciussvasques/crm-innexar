# Stripe Webhook & Dynadot – Configuração e Testes

## Stripe Webhook

### Evento usado
- **`checkout.session.completed`** – disparado quando o cliente conclui o pagamento no Checkout.

### URLs do webhook
O backend expõe o handler em dois caminhos (use **um** no Stripe Dashboard):

| URL | Uso |
|-----|-----|
| `https://<CRM_HOST>/api/site-orders/webhook` | Direto no router de site-orders |
| `https://<CRM_HOST>/api/launch/webhook` | Proxy em launch (recomendado se o Stripe já aponta para /api/launch/webhook) |

Substitua `<CRM_HOST>` por seu domínio (ex: `sales.innexar.app`).

### Configuração no Stripe Dashboard
1. **Developers** → **Webhooks** → **Add endpoint**
2. **Endpoint URL**: `https://sales.innexar.app/api/launch/webhook` (ou `/api/site-orders/webhook`)
3. **Events to send**: marque **`checkout.session.completed`**
4. Copie o **Signing secret** (`whsec_...`) e salve em **CRM → Settings → Stripe → Stripe Webhook Secret**

### O que o handler faz ao receber `checkout.session.completed`
1. Cria ou atualiza o pedido (idempotente por `stripe_session_id`)
2. Cria subscription de hosting (trial 90 dias) se `stripe_hosting_price_id` e `stripe_customer_id` estiverem configurados
3. Envia email de confirmação de pagamento

### Teste rápido (Stripe CLI)
```bash
stripe listen --forward-to https://sales.innexar.app/api/launch/webhook
# Em outro terminal:
stripe trigger checkout.session.completed
```

---

## Dynadot

### Configuração no CRM
- **Settings** → **Dynadot**
- **Dynadot API Key** (secret)
- **Dynadot API Secret** (secret)
- **Maximum domain price** – valor máximo (USD) para oferecer domínio “grátis” (ex: 15.00)

### Teste
- Após preencher as chaves e salvar, a integração de **verificação de disponibilidade** e **registro** de domínio (quando implementada) usará essas configs.
- Para validar só as configs: confira em Settings se os campos são salvos e se não há erro ao carregar a página.

---

## Resumo do que foi implementado (conversa)

| Item | Onde |
|------|------|
| Webhook `checkout.session.completed` | Backend: `site_orders.py` + `launch.py` |
| Subscription de hosting (trial 90 dias) | Backend: webhook + `stripe_service.create_hosting_subscription` |
| Campos Stripe (hosting price, trial days) | Backend: `system_config` DEFAULT_CONFIGS + seed no startup |
| Campos Dynadot (API key, secret, max price) | Backend: `system_config` + front CRM: Settings → Dynadot |
| Campo domínio no onboarding | Backend: `SiteOnboarding.desired_domain` + API; Site: onboarding step 1; CRM: Briefing Overview |
| Aba Communication (chat) no CRM | Front CRM: modal do pedido → aba "Communication" |
| Landing: logo grátis, 3 meses hosting, $9.99/mês | Site: launch page (features + pricing) |

### Migração: campo domínio no onboarding
Para ativar o campo "Domínio desejado" no onboarding, rode a migração (uma vez):

```bash
cd /opt/innexar-crm/backend
python -m migrations.add_desired_domain
```

Ou no PostgreSQL:
```sql
ALTER TABLE site_onboardings ADD COLUMN IF NOT EXISTS desired_domain VARCHAR NULL;
```
