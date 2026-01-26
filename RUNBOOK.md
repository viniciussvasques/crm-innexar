# Runbook

## Ambiente de Desenvolvimento

### Frontend
```bash
cd frontend
npm install
npm run dev
# URL: http://localhost:3000
```

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# URL: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## Como Rodar Testes
### Backend
```bash
pytest
```
### Frontend
```bash
npm run test
```

## Deploy (Produção)
1.  **Build**:
    - Build Docker images (`frontend:latest`, `backend:latest`).
    - Push para Registry.
2.  **Migrate**:
    - Executar `alembic upgrade head` no container backend.
3.  **Deploy**:
    - Atualizar ECS/Kubernetes/Docker Compose com nova tag.

## Rollback
1.  **Revert**: Reverter versão da imagem no orquestrador.
2.  **Database**: Se houve migração destrutiva, rodar `alembic downgrade -1` (CUIDADO).

## Debug
-   Verificar logs via `docker logs` ou AWS CloudWatch.
-   Verificar status do Stripe em Dashboard.
-   Verificar filas Redis se IA não responder.
