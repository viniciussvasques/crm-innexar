# API Documentation

Base URL: `/api/v1` (ou `/api`)

## Auth (`/api/auth`)
-   `POST /login`: Retorna Access Token.
-   `POST /register`: Cria conta inicial.
-   `POST /refresh`: Renova token.

## Orders (`/api/orders`)
-   `GET /`: Lista pedidos do usuário.
-   `POST /`: Cria novo pedido com requisitos (Onboarding Data).
-   `GET /{id}`: Detalhes e Status de progresso.

## AI Configuration (`/api/ai-config`)
-   `GET /`: Lista provedores configurados.
-   `POST /`: Adiciona provedor.
-   `POST /fetch-models`: Proxy para listar modelos do provedor.
-   `GET /router-rules`: Regras de roteamento de modelos.
-   `POST /router-rules`: Atualiza regra.

## Webhooks (`/api/webhooks`)
-   `POST /stripe`: Eventos de pagamento (`checkout.session.completed`).

## Deploy Servers (`/api/config/deploy-servers`)
-   `GET /`: Lista servidores.
-   `POST /`: Adiciona servidor (SSH/FTP).

## Erros
-   401: Unauthorized.
-   403: Forbidden (Tenant limit or Role).
-   422: Validation Error (Pydantic).
-   500: Server Error.
