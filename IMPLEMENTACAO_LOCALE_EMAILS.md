# ✅ Implementação de Locale nos Emails

## 🎯 Objetivo
Emails devem ser enviados no idioma do navegador do cliente no momento do cadastro/onboarding.

## ✅ Implementado

### 1. Database
- ✅ Adicionada coluna `preferred_locale` na tabela `site_customers`
- ✅ Migration executada com sucesso
- ✅ Valores padrão: `'en'` para clientes existentes

### 2. Backend - Modelos
- ✅ `SiteCustomer.preferred_locale` adicionado ao modelo
- ✅ `SiteOnboardingCreate.locale` adicionado (opcional)

### 3. Backend - Serviços
- ✅ `create_customer_account()` agora aceita `locale` e salva em `preferred_locale`
- ✅ `OnboardingService` captura locale do onboarding_data e passa para criação de conta
- ✅ `EmailService` atualizado:
  - Método `_normalize_locale()` para normalizar códigos (pt-BR → pt)
  - Todos os métodos de email agora usam locale nas URLs:
    - `send_payment_confirmation` - URLs com `/{locale}/launch/...`
    - `send_onboarding_complete` - URLs com locale
    - `send_site_in_progress` - URLs com locale
    - `send_ready_for_review` - URLs com locale
    - `send_site_delivered` - URLs com locale
    - `send_verification_email` - aceita parâmetro `locale`
    - `send_password_reset_email` - aceita parâmetro `locale`

### 4. Backend - APIs
- ✅ `POST /api/site-orders/{id}/onboarding` - aceita `locale` no body
- ✅ `POST /api/emails/send-onboarding-complete/{id}?locale=pt` - aceita locale via query param
- ✅ `order_to_dict()` busca `preferred_locale` do customer quando disponível
- ✅ Endpoints de preview/delivery buscam locale do customer

### 5. Frontend - Website
- ✅ Página de onboarding captura `locale` via `useLocale()` do next-intl
- ✅ Envia `locale` no payload do POST `/api/launch/onboarding`
- ✅ Rota `/api/launch/onboarding` extrai locale da URL e passa para CRM

## 🔄 Fluxo Completo

```
1. Cliente acessa /pt/launch/onboarding (ou /en/, /es/)
2. Website captura locale = 'pt' via useLocale()
3. Cliente completa onboarding → POST com locale: 'pt'
4. Backend cria SiteCustomer com preferred_locale = 'pt'
5. Email de verificação enviado com URLs /pt/launch/verify-email
6. Email de onboarding complete com URLs /pt/launch/dashboard
7. Todos os emails subsequentes usam preferred_locale do customer
```

## 📝 URLs Atualizadas

Todos os emails agora usam:
- **Antes**: `https://innexar.app/en/launch/...`
- **Depois**: `https://innexar.app/{locale}/launch/...`

Onde `{locale}` vem de:
1. Query param `?locale=pt` (prioridade)
2. `customer.preferred_locale` (fallback)
3. `'en'` (default final)

## ✅ Status
- ✅ Migrations executadas
- ✅ Backend reiniciado sem erros
- ✅ Pronto para testes
