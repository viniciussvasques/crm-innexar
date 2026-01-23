# Regras de Desenvolvimento - AI Site Generator

## 🧠 Princípio Fundamental

> **Nada é criado sem verificação. Nada é consumido sem contrato. Nada é alterado sem análise de impacto.**

---

## 1. Arquitetura e Design

### 1.1 Separação de Responsabilidades

```
┌─────────────────────────────────────────────────────────────────┐
│                     CAMADAS DO SISTEMA                          │
├─────────────────────────────────────────────────────────────────┤
│  API Layer      │ Endpoints, validação, autenticação           │
│  Service Layer  │ Lógica de negócio, orquestração              │
│  Repository     │ Acesso ao banco de dados                      │
│  External       │ Integrações (GitHub, Cloudflare, IA)         │
│  Worker Layer   │ Jobs assíncronos, pipeline                    │
└─────────────────────────────────────────────────────────────────┘
```

**Regra:** Cada camada só se comunica com a adjacente. API nunca acessa Repository diretamente.

### 1.2 IA Não Executa, Apenas Produz

```python
# ✅ CORRETO
def generate_patch(context: dict) -> str:
    """IA retorna string com diff"""
    response = ai_service.generate(prompt, context)
    return response.content  # Retorna texto/JSON

# ❌ INCORRETO  
def generate_and_apply_patch(context: dict):
    """IA nunca deve executar ações"""
    response = ai_service.generate(prompt, context)
    git.apply(response.content)  # IA não deve fazer isso
```

### 1.3 Failsafe por Padrão

```python
# Toda operação tem fallback
@celery.task(
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(TransientError,)
)
def generate_code_patch(project_id: str):
    try:
        # Tentar geração
        pass
    except PermanentError:
        # Falha definitiva → escalar para humano
        create_human_task(project_id, "Code generation failed")
```

---

## 2. API e Contratos

### 2.1 Todo Endpoint Tem Contrato

Antes de implementar qualquer endpoint:

```yaml
# Definir explicitamente:
endpoint: POST /projects/{id}/generate
method: POST
auth: required (JWT)
request_body:
  type: object
  properties: {}
response:
  201:
    schema: GenerateResponse
  400:
    schema: ValidationError
  404:
    schema: NotFoundError
```

### 2.2 Erros Estruturados

```python
# ✅ CORRETO
class APIError(Exception):
    def __init__(self, code: str, message: str, field: str = None):
        self.code = code
        self.message = message
        self.field = field

# Response
{
    "error": {
        "code": "PROJECT_NOT_FOUND",
        "message": "Projeto não encontrado",
        "field": null
    }
}

# ❌ INCORRETO
raise Exception("Projeto não encontrado")
```

### 2.3 Validação em Todas as Camadas

```python
# API Layer - validação de formato
@router.post("/projects")
async def create_project(data: CreateProjectRequest):  # Pydantic valida
    pass

# Service Layer - validação de negócio
class ProjectService:
    async def create(self, data: CreateProjectRequest):
        if await self.exists_by_slug(data.slug):
            raise BusinessError("SLUG_EXISTS", "Slug já existe")
```

---

## 3. Banco de Dados

### 3.1 Migrations São Obrigatórias

```bash
# Nunca alterar banco diretamente
# Sempre usar Alembic

alembic revision --autogenerate -m "add_site_spec_table"
alembic upgrade head
```

### 3.2 Toda Coluna Documentada

```python
class Project(Base):
    __tablename__ = "project"
    
    id = Column(UUID, primary_key=True, doc="Identificador único")
    status = Column(
        String(50), 
        nullable=False,
        doc="Status: pending, generating, preview_ready, delivered"
    )
```

### 3.3 Índices Explícitos

```python
# Criar índice para queries frequentes
__table_args__ = (
    Index('idx_project_customer', 'customer_id'),
    Index('idx_project_status', 'status'),
)
```

---

## 4. Código Python

### 4.1 Type Hints Obrigatórios

```python
# ✅ CORRETO
async def create_project(
    customer_id: UUID,
    template_id: str,
    name: str
) -> Project:
    pass

# ❌ INCORRETO
async def create_project(customer_id, template_id, name):
    pass
```

### 4.2 Docstrings em Funções Públicas

```python
async def generate_site_spec(project_id: UUID) -> SiteSpec:
    """Gera especificação do site a partir do onboarding.
    
    Args:
        project_id: ID do projeto
        
    Returns:
        SiteSpec com configuração completa do site
        
    Raises:
        OnboardingNotFoundError: Se onboarding não existe
        AIServiceError: Se IA falhar após retries
    """
    pass
```

### 4.3 Async/Await Consistente

```python
# ✅ CORRETO - Todo I/O é async
async def process_project(project_id: UUID):
    project = await project_repo.get(project_id)
    spec = await ai_service.generate_spec(project)
    await artifact_repo.save(spec)

# ❌ INCORRETO - Misturar sync e async
def process_project(project_id: UUID):
    project = project_repo.get(project_id)  # Bloqueia event loop
```

---

## 5. Frontend (TypeScript/React)

### 5.1 Componentes Tipados

```typescript
// ✅ CORRETO
interface ProjectCardProps {
  project: Project;
  onEdit: (id: string) => void;
  isLoading?: boolean;
}

export function ProjectCard({ project, onEdit, isLoading }: ProjectCardProps) {
  // ...
}

// ❌ INCORRETO
export function ProjectCard(props: any) {
  // ...
}
```

### 5.2 Estados Obrigatórios

Toda tela deve tratar:

```typescript
// Estados obrigatórios
type PageState = 
  | { status: 'loading' }
  | { status: 'error'; error: APIError }
  | { status: 'empty' }
  | { status: 'success'; data: T };

// Implementação
function ProjectsPage() {
  if (state.status === 'loading') return <Loading />;
  if (state.status === 'error') return <Error error={state.error} />;
  if (state.status === 'empty') return <EmptyState />;
  return <ProjectList data={state.data} />;
}
```

### 5.3 Hooks Customizados para API

```typescript
// ✅ CORRETO - Hook reutilizável
function useProjects() {
  const { data, error, isLoading, mutate } = useSWR('/api/projects', fetcher);
  return { projects: data, error, isLoading, refresh: mutate };
}

// ❌ INCORRETO - Fetch direto no componente
function ProjectsPage() {
  const [data, setData] = useState();
  useEffect(() => {
    fetch('/api/projects').then(r => r.json()).then(setData);
  }, []);
}
```

---

## 6. Workers e Jobs

### 6.1 Tasks Idempotentes

```python
# ✅ CORRETO - Pode rodar múltiplas vezes sem efeito colateral
@celery.task
def generate_brief(project_id: str):
    existing = await artifact_repo.get(project_id, "brief")
    if existing:
        return existing.id  # Já existe, retorna
    
    brief = await ai_service.generate_brief(project_id)
    return await artifact_repo.save(brief)

# ❌ INCORRETO - Cria duplicatas
@celery.task
def generate_brief(project_id: str):
    brief = await ai_service.generate_brief(project_id)
    return await artifact_repo.save(brief)  # Sempre cria novo
```

### 6.2 Timeout Explícito

```python
@celery.task(
    time_limit=600,      # 10 minutos máximo
    soft_time_limit=540  # Aviso em 9 minutos
)
def build_and_test(project_id: str):
    pass
```

### 6.3 Logging Estruturado

```python
import structlog

logger = structlog.get_logger()

@celery.task
def generate_code_patch(project_id: str):
    logger.info("Starting code generation", project_id=project_id)
    try:
        result = await process()
        logger.info("Code generated", project_id=project_id, lines=result.lines)
    except Exception as e:
        logger.error("Code generation failed", project_id=project_id, error=str(e))
        raise
```

---

## 7. Integrações Externas

### 7.1 Wrapper para Cada Integração

```python
# Serviço dedicado para cada integração
class GitHubService:
    def __init__(self, config: GitHubConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={"Authorization": f"Bearer {config.access_token}"}
        )
    
    async def create_repo(self, name: str) -> str:
        # Lógica encapsulada
        pass
```

### 7.2 Retry com Backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
async def call_ai_api(prompt: str) -> str:
    response = await self.client.post("/v1/messages", json={...})
    response.raise_for_status()
    return response.json()
```

### 7.3 Rate Limiting

```python
from asyncio import Semaphore

class AIService:
    def __init__(self):
        self.semaphore = Semaphore(5)  # Máximo 5 chamadas simultâneas
    
    async def generate(self, prompt: str) -> str:
        async with self.semaphore:
            return await self._call_api(prompt)
```

---

## 8. Segurança

### 8.1 Secrets Nunca em Código

```python
# ✅ CORRETO - Variáveis de ambiente
import os
API_KEY = os.environ["GITHUB_TOKEN"]

# ❌ INCORRETO - Hardcoded
API_KEY = "ghp_xxxxxxxxxxxx"
```

### 8.2 Validação de Input

```python
# Validar TUDO que vem de fora
from pydantic import BaseModel, validator

class OnboardingSubmission(BaseModel):
    business_name: str
    
    @validator('business_name')
    def validate_name(cls, v):
        if len(v) > 200:
            raise ValueError("Nome muito longo")
        if re.search(r'[<>\"\'&]', v):
            raise ValueError("Caracteres inválidos")
        return v
```

### 8.3 Allowlist para Arquivos Editáveis

```python
EDITABLE_FILES = [
    "src/content/**/*.json",
    "src/components/sections/**/*.tsx",
    "public/images/**/*",
]

def is_editable(file_path: str) -> bool:
    return any(fnmatch(file_path, pattern) for pattern in EDITABLE_FILES)

def apply_patch(patch: str, project: Project):
    files = extract_files_from_patch(patch)
    for file in files:
        if not is_editable(file):
            raise SecurityError(f"Arquivo não editável: {file}")
```

---

## 9. Testes

### 9.1 Cobertura Mínima

- **Services**: 80%
- **API Endpoints**: 90%
- **Utilitários**: 70%

### 9.2 Tipos de Teste

```python
# Unit Test - Lógica isolada
def test_transform_onboarding_to_spec():
    onboarding = {"business_name": "Test"}
    spec = transform_onboarding(onboarding)
    assert spec.business.name == "Test"

# Integration Test - Com dependências reais
@pytest.mark.integration
async def test_create_project_flow():
    project = await project_service.create(...)
    assert project.status == "pending"
    assert await pipeline_step_repo.count(project.id) == 12

# E2E Test - Fluxo completo
@pytest.mark.e2e
async def test_full_generation_pipeline():
    # Cria projeto, roda pipeline, verifica deploy
    pass
```

### 9.3 Mocks para Integrações

```python
@pytest.fixture
def mock_github(mocker):
    mock = mocker.patch("services.github.GitHubService")
    mock.create_repo.return_value = "https://github.com/org/repo"
    return mock

async def test_provision_repo(mock_github):
    result = await project_service.provision_repo(project_id)
    mock_github.create_repo.assert_called_once()
```

---

## 10. Git e Deploy

### 10.1 Commits Semânticos

```
feat: Adiciona geração de brief via IA
fix: Corrige timeout em build_and_test
docs: Atualiza documentação de API
refactor: Extrai lógica de validação
test: Adiciona testes para ProjectService
chore: Atualiza dependências
```

### 10.2 Branch Strategy

```
main        → Produção
develop     → Desenvolvimento
feature/*   → Features
fix/*       → Correções
release/*   → Preparação de release
```

### 10.3 PR Checklist

- [ ] Testes passando
- [ ] Lint sem erros
- [ ] Type check sem erros
- [ ] Documentação atualizada
- [ ] Migration criada (se necessário)
- [ ] Review por pelo menos 1 pessoa

---

## 11. Monitoramento

### 11.1 Logs Obrigatórios

```python
# Início e fim de operações importantes
logger.info("Starting pipeline", project_id=id)
logger.info("Pipeline completed", project_id=id, duration=seconds)

# Erros com contexto
logger.error("Pipeline failed", 
    project_id=id, 
    step=step_key, 
    error=str(e),
    traceback=traceback.format_exc()
)
```

### 11.2 Métricas

```python
from prometheus_client import Counter, Histogram

pipeline_duration = Histogram(
    'pipeline_duration_seconds',
    'Tempo de execução do pipeline',
    ['template_id']
)

pipeline_errors = Counter(
    'pipeline_errors_total',
    'Total de erros no pipeline',
    ['step', 'error_type']
)
```

---

## 12. Checklist de Desenvolvimento

### Antes de Começar

- [ ] Feature documentada em FEATURES.md
- [ ] API contract definido
- [ ] Schema de dados definido
- [ ] Impacto em outras features analisado

### Durante Desenvolvimento

- [ ] Type hints em todo código
- [ ] Docstrings em funções públicas
- [ ] Validação de inputs
- [ ] Tratamento de erros
- [ ] Logs estruturados
- [ ] Testes escritos

### Antes do PR

- [ ] `npm run lint` passa
- [ ] `npm run typecheck` passa
- [ ] `pytest` passa
- [ ] Documentação atualizada
- [ ] Code review solicitado

---

*Última atualização: Janeiro 2026*
