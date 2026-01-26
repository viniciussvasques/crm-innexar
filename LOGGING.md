# Logging Standards

## Principles
1.  **Observabilidade**: Logs devem permitir rastrear uma requisição do início ao fim (`request_id`).
2.  **Segurança**: NUNCA logar Informações Pessoais Identificáveis (PII) ou Segredos.
3.  **Estrutura**: Preferência por JSON estruturado em produção.

## Níveis de Log
-   **ERROR**: Erros que impedem o funcionamento (Ex: Falha DB,Exception não tratada). Dispara alerta.
-   **WARN**: Situações anômalas mas recuperáveis (Ex: Login falhou, Retentativa de Stripe).
-   **INFO**: Eventos de negócio significativos (Ex: "Pedido #123 criado", "Onboarding completo").
-   **DEBUG**: Informações técnicas para dev (Ex: Payload de webhook, query SQL). Desativado em prod.

## O Que NUNCA Logar
-   Senhas ou Hashes.
-   Tokens JWT ou API Keys (OpenAI, Stripe).
-   Dados de cartão de crédito.
-   Emails de clientes (use ID ou hash se necessário).

## Formato (Exemplo)
```json
{
  "timestamp": "2023-10-27T10:00:00Z",
  "level": "INFO",
  "service": "backend-api",
  "request_id": "req-12345",
  "user_id": 42,
  "event": "order_created",
  "data": {
    "order_id": 100,
    "amount": 299.00
  }
}
```
