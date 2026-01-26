# Security Policy

## Gerenciamento de Segredos
-   **NUNCA** commitar `.env` ou chaves no Git.
-   Em produção, usar Injeção de Variáveis de Ambiente (AWS Secrets Manager, Vault).
-   Chaves de API (Stripe, OpenAI) devem ser rotacionadas a cada 90 dias ou imediatamente após suspeita de vazamento.

## Autenticação
-   JWT com expiração curta (15min Access, 7d Refresh).
-   Senhas hash com `bcrypt` ou `argon2`.
-   MFA recomendado para Admins.

## Escopos e Permissões
-   Princípio do Privilégio Mínimo.
-   Serviço de IA tem acesso apenas a tabelas de Config e Orders.
-   Webhook Stripe valida assinatura criptográfica.

## Resposta a Incidentes
1.  **Identificar**: Monitoramento alerta anomalia.
2.  **Conter**: Revogar tokens comprometidos, bloquear IPs.
3.  **Erradicar**: Corrigir vulnerabilidade (Patch).
4.  **Recuperar**: Restaurar integridade dos dados.
5.  **Post-Mortem**: Documentar lições aprendidas.
