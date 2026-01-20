# 🚀 Innexar CRM - MVP

CRM interno da Innexar focado em vendedores e monitoramento.

## 🏗️ Stack

- **Backend:** FastAPI + PostgreSQL + Redis
- **Frontend:** Next.js 14 + Tailwind CSS
- **Deploy:** Docker Compose + Traefik

## 🚀 Início Rápido

### 1. Configurar variáveis de ambiente

```bash
cp env.example .env
# Edite .env com suas configurações
```

### 2. Subir os containers

```bash
docker compose up -d
```

### 3. Criar primeiro usuário admin

```bash
docker compose exec backend python -m app.scripts.create_admin
```

Ou via API:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@innexar.app",
    "name": "Admin",
    "password": "senha_forte",
    "role": "admin"
  }'
```

### 4. Acessar

- **Frontend:** https://crm.innexar.app
- **API:** https://api.crm.innexar.app
- **Docs API:** https://api.crm.innexar.app/docs

## 📁 Estrutura

```
innexar-crm/
├── backend/          # FastAPI
├── frontend/         # Next.js
├── docker-compose.yml
└── README.md
```

## 🔐 Usuários

- **Admin:** Acesso total, pode ver todos os vendedores
- **Vendedor:** Vê apenas seus próprios contatos/oportunidades

## 📊 Funcionalidades MVP

- ✅ Autenticação (login/logout)
- ✅ Gestão de usuários (admin)
- ✅ Contatos (CRUD)
- ✅ Oportunidades (CRUD + Pipeline)
- ✅ Atividades (Tarefas, Ligações, Reuniões, Notas)
- ✅ Dashboard Vendedor
- ✅ Dashboard Admin (monitoramento)

## 🛠️ Desenvolvimento

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📝 Notas

- Banco de dados é criado automaticamente na primeira execução
- Migrations serão adicionadas em breve
- Para produção, altere SECRET_KEY e senhas no .env

