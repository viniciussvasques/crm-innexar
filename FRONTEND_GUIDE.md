# Frontend Guide

## Estrutura de Pastas
-   `src/app`: App Router (Pages, Layouts).
-   `src/components`: UI e Feature components.
    -   `/ui`: Atomos (Button, Input).
-   `src/lib`: Utils (api client, formatters).
-   `src/hooks`: Custom hooks.

## Estado Global
-   Uso de **React Context** para sessões leves.
-   Uso de **React Query** (ou useEffect manual por enquanto) para Server State.
-   **NÃO** usar Redux a menos que extremamente necessário.

## Padrão de Componentes
-   **Server Components** por padrão.
-   `'use client'` apenas quando houver interatividade (useState, onClick).
-   Componentes visuais isolados em `src/components/ui`.

## Padrão de Forms
-   Usar `react-hook-form` + `zod` para validação.
-   Componentes de formulário controlados.

## Comunicação com API
-   Instância Axios em `src/lib/api.ts`.
-   Interceptores para anexar Token JWT automaticamente.
-   Tratamento de erro centralizado (Toast notification).
