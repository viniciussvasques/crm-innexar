# Arquitetura Worker e Runner - AI Site Generator

## Visão Geral do Sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARQUITETURA DE PROCESSAMENTO                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐                                                           │
│   │   FastAPI   │◄─── Requests HTTP                                         │
│   │    (API)    │                                                           │
│   └──────┬──────┘                                                           │
│          │                                                                   │
│          │ Enqueue Job                                                       │
│          ▼                                                                   │
│   ┌─────────────┐                                                           │
│   │    Redis    │◄─── Message Broker + Cache                                │
│   │   (Queue)   │                                                           │
│   └──────┬──────┘                                                           │
│          │                                                                   │
│          │ Consume Task                                                      │
│          ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        CELERY WORKERS                               │   │
│   ├─────────────────────────────────────────────────────────────────────┤   │
│   │                                                                      │   │
│   │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │   │
│   │   │   Worker    │    │   Worker    │    │   Worker    │            │   │
│   │   │  (General)  │    │    (AI)     │    │   (Build)   │            │   │
│   │   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘            │   │
│   │          │                  │                  │                    │   │
│   │          ▼                  ▼                  ▼                    │   │
│   │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │   │
│   │   │  Postgres   │    │ AI Service  │    │Build Runner │            │   │
│   │   │  (State)    │    │ (Claude/GPT)│    │  (Docker)   │            │   │
│   │   └─────────────┘    └─────────────┘    └─────────────┘            │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Celery Workers

### Tipos de Workers

| Worker | Responsabilidade | Concorrência | Recursos |
|--------|------------------|--------------|----------|
| **General** | Validação, DB ops, notificações | 4 | 1 CPU, 512MB |
| **AI** | Chamadas para LLMs | 2 | 1 CPU, 1GB |
| **Build** | Git, npm, build | 1 | 2 CPU, 4GB |

### Configuração Celery

```python
# celery_config.py
from celery import Celery

app = Celery('site_generator')

app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    
    # Filas separadas por tipo
    task_routes={
        'tasks.ai.*': {'queue': 'ai'},
        'tasks.build.*': {'queue': 'build'},
        'tasks.*': {'queue': 'general'},
    },
    
    # Retry
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Timeouts
    task_time_limit=600,  # 10 minutos max
    task_soft_time_limit=540,  # Aviso em 9 min
    
    # Resultados expiram em 24h
    result_expires=86400,
)
```

### Iniciar Workers

```bash
# Worker geral (4 processos)
celery -A app.celery worker -Q general -c 4 --loglevel=info

# Worker IA (2 processos, rate limited)
celery -A app.celery worker -Q ai -c 2 --loglevel=info

# Worker Build (1 processo, isolado)
celery -A app.celery worker -Q build -c 1 --loglevel=info
```

---

## 2. Tasks do Pipeline

### Estrutura de Tasks

```python
# tasks/__init__.py
from celery import shared_task
from app.services import ai_service, github_service, build_service

# ─────────────────────────────────────────────────────────────
# FASE 1: INGESTÃO
# ─────────────────────────────────────────────────────────────

@shared_task(bind=True, queue='general', max_retries=3)
def validate_onboarding(self, project_id: str):
    """Valida dados do onboarding"""
    try:
        project = get_project(project_id)
        onboarding = get_onboarding(project_id)
        
        errors = validate_required_fields(onboarding)
        if errors:
            update_step_status(project_id, 'validate_onboarding', 'failed', errors)
            return {'success': False, 'errors': errors}
        
        update_step_status(project_id, 'validate_onboarding', 'success')
        
        # Encadear próxima task
        download_assets.delay(project_id)
        return {'success': True}
        
    except Exception as e:
        self.retry(exc=e)


@shared_task(bind=True, queue='general', max_retries=3)
def download_assets(self, project_id: str):
    """Baixa assets (logo, imagens) para R2"""
    try:
        onboarding = get_onboarding(project_id)
        assets = []
        
        for asset in onboarding.get('assets', []):
            url = storage_service.upload(asset['file'], project_id)
            assets.append({'type': asset['type'], 'url': url})
        
        save_assets_manifest(project_id, assets)
        update_step_status(project_id, 'download_assets', 'success')
        
        create_site_spec.delay(project_id)
        return {'success': True, 'assets': assets}
        
    except Exception as e:
        self.retry(exc=e)


# ─────────────────────────────────────────────────────────────
# FASE 2: DOCUMENTAÇÃO (IA)
# ─────────────────────────────────────────────────────────────

@shared_task(bind=True, queue='ai', max_retries=2, rate_limit='5/m')
def generate_brief(self, project_id: str):
    """IA gera brief do projeto"""
    try:
        site_spec = get_site_spec(project_id)
        
        # Chamar IA
        result = ai_service.generate(
            task_type='brief',
            context={
                'business': site_spec['business'],
                'industry': site_spec['business']['industry']
            }
        )
        
        if not result.success:
            raise AIGenerationError(result.error)
        
        # Salvar artefato
        save_artifact(project_id, 'brief', result.content)
        update_step_status(project_id, 'generate_brief', 'success')
        
        generate_sitemap.delay(project_id)
        return {'success': True}
        
    except Exception as e:
        self.retry(exc=e)


@shared_task(bind=True, queue='ai', max_retries=2, rate_limit='5/m')
def generate_content(self, project_id: str):
    """IA gera conteúdo de cada página"""
    try:
        site_spec = get_site_spec(project_id)
        sitemap = get_artifact(project_id, 'sitemap')
        
        content = {}
        for page in sitemap['pages']:
            result = ai_service.generate(
                task_type='page_content',
                context={
                    'page': page,
                    'business': site_spec['business'],
                    'tone': site_spec['design']['tone']
                }
            )
            content[page['slug']] = result.content
        
        save_artifact(project_id, 'content', content)
        update_step_status(project_id, 'generate_content', 'success')
        
        # PAUSA: Aguarda aprovação do cliente
        update_project_status(project_id, 'awaiting_content')
        create_content_approvals(project_id, content)
        
        return {'success': True, 'awaiting_approval': True}
        
    except Exception as e:
        self.retry(exc=e)


# ─────────────────────────────────────────────────────────────
# FASE 3: PROJETO GIT
# ─────────────────────────────────────────────────────────────

@shared_task(bind=True, queue='general', max_retries=2)
def provision_repository(self, project_id: str):
    """Cria repositório no GitHub"""
    try:
        project = get_project(project_id)
        template_id = project.template_id
        
        repo_url = github_service.create_repo_from_template(
            template_key=template_id,
            project_slug=project.slug
        )
        
        update_project(project_id, {'repo_url': repo_url})
        update_step_status(project_id, 'provision_repository', 'success')
        
        setup_structure.delay(project_id)
        return {'success': True, 'repo_url': repo_url}
        
    except Exception as e:
        self.retry(exc=e)


# ─────────────────────────────────────────────────────────────
# FASE 4: GERAÇÃO DE CÓDIGO (IA + BUILD)
# ─────────────────────────────────────────────────────────────

@shared_task(bind=True, queue='ai', max_retries=2, rate_limit='5/m')
def generate_code_patches(self, project_id: str):
    """IA gera patches de código"""
    try:
        site_spec = get_site_spec(project_id)
        content = get_artifact(project_id, 'content')
        layout_plan = get_artifact(project_id, 'layout_plan')
        
        patches = []
        for page in layout_plan['pages']:
            result = ai_service.generate(
                task_type='code_patch',
                context={
                    'page': page,
                    'content': content[page['slug']],
                    'template_structure': get_template_structure(site_spec['design']['template_id'])
                }
            )
            patches.append({
                'file': page['file_path'],
                'patch': result.content
            })
        
        save_artifact(project_id, 'code_patches', patches)
        update_step_status(project_id, 'generate_code_patches', 'success')
        
        apply_patches.delay(project_id)
        return {'success': True}
        
    except Exception as e:
        self.retry(exc=e)


@shared_task(bind=True, queue='build', max_retries=1, time_limit=600)
def apply_patches(self, project_id: str):
    """Aplica patches no repositório (via Build Runner)"""
    try:
        project = get_project(project_id)
        patches = get_artifact(project_id, 'code_patches')
        
        # Executa no Build Runner isolado
        result = build_runner.apply_patches(
            repo_url=project.repo_url,
            branch=f'preview-{project_id}',
            patches=patches
        )
        
        if not result.success:
            raise PatchApplicationError(result.error)
        
        update_step_status(project_id, 'apply_patches', 'success')
        
        build_and_test.delay(project_id)
        return {'success': True, 'commit_sha': result.commit_sha}
        
    except Exception as e:
        # Se falhar, tenta regenerar patches
        if self.request.retries < 1:
            regenerate_and_fix.delay(project_id, str(e))
        else:
            escalate_to_human(project_id, 'apply_patches', str(e))
        raise


@shared_task(bind=True, queue='build', max_retries=3, time_limit=600)
def build_and_test(self, project_id: str):
    """Executa build e testes (via Build Runner)"""
    try:
        project = get_project(project_id)
        
        result = build_runner.build_project(
            repo_url=project.repo_url,
            branch=f'preview-{project_id}'
        )
        
        save_artifact(project_id, 'build_report', result.report)
        
        if not result.success:
            # Tenta correção automática
            if self.request.retries < 2:
                fix_result = ai_service.generate(
                    task_type='fix_build_error',
                    context={'error': result.error, 'logs': result.logs}
                )
                apply_fix_patch.delay(project_id, fix_result.content)
                raise BuildError(result.error)
            else:
                escalate_to_human(project_id, 'build_and_test', result.error)
                raise
        
        update_step_status(project_id, 'build_and_test', 'success')
        
        deploy_preview.delay(project_id)
        return {'success': True}
        
    except Exception as e:
        self.retry(exc=e)
```

---

## 3. Build Runner (Isolado)

### Por que isolado?

1. **Segurança**: Código do cliente não acessa nossa infra
2. **Recursos**: Builds consomem muita CPU/RAM
3. **Previsibilidade**: Ambiente limpo a cada build
4. **Timeout**: Fácil matar container travado

### Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BUILD RUNNER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐      ┌─────────────────────────────────────────────────┐  │
│   │   Celery    │      │              Docker Container                   │  │
│   │   Worker    │─────▶│   ┌─────────────────────────────────────────┐   │  │
│   │   (Build)   │      │   │          Build Script                   │   │  │
│   └─────────────┘      │   │                                         │   │  │
│                        │   │  1. git clone repo                      │   │  │
│                        │   │  2. git checkout branch                 │   │  │
│                        │   │  3. Apply patches                       │   │  │
│                        │   │  4. npm install                         │   │  │
│                        │   │  5. npm run build                       │   │  │
│                        │   │  6. npm run test (opcional)             │   │  │
│                        │   │  7. Zip artifacts                       │   │  │
│                        │   │                                         │   │  │
│                        │   └─────────────────────────────────────────┘   │  │
│                        │                                                  │  │
│                        │   Recursos: 2 CPU, 4GB RAM                      │  │
│                        │   Timeout: 10 minutos                           │  │
│                        │   Network: Git + NPM registry only              │  │
│                        └─────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementação

```python
# services/build_runner.py
import docker
import tempfile
from pathlib import Path

class BuildRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.image = "innexar/build-runner:latest"
        self.timeout = 600  # 10 minutos
    
    async def build_project(
        self, 
        repo_url: str, 
        branch: str
    ) -> BuildResult:
        """Executa build em container isolado"""
        
        # Criar diretório temporário para output
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            try:
                container = self.client.containers.run(
                    image=self.image,
                    command=[
                        "/bin/bash", "-c",
                        f"""
                        git clone {repo_url} /app &&
                        cd /app &&
                        git checkout {branch} &&
                        npm ci --legacy-peer-deps &&
                        npm run build &&
                        cp -r .next/static /output/ &&
                        echo "BUILD_SUCCESS"
                        """
                    ],
                    volumes={
                        str(output_dir): {'bind': '/output', 'mode': 'rw'}
                    },
                    mem_limit='4g',
                    cpu_count=2,
                    network_mode='bridge',  # Acesso limitado
                    remove=True,
                    timeout=self.timeout
                )
                
                logs = container.decode('utf-8')
                
                if "BUILD_SUCCESS" in logs:
                    return BuildResult(
                        success=True,
                        logs=logs,
                        artifacts_path=str(output_dir)
                    )
                else:
                    return BuildResult(
                        success=False,
                        error="Build failed",
                        logs=logs
                    )
                    
            except docker.errors.ContainerError as e:
                return BuildResult(
                    success=False,
                    error=str(e),
                    logs=e.stderr.decode('utf-8') if e.stderr else ""
                )
            except docker.errors.APIError as e:
                return BuildResult(
                    success=False,
                    error=f"Docker API error: {e}"
                )
    
    async def apply_patches(
        self, 
        repo_url: str, 
        branch: str, 
        patches: list[dict]
    ) -> PatchResult:
        """Aplica patches e commita"""
        
        # Serializar patches para o container
        patches_json = json.dumps(patches)
        
        container = self.client.containers.run(
            image=self.image,
            command=[
                "/bin/bash", "-c",
                f"""
                git clone {repo_url} /app &&
                cd /app &&
                git checkout -b {branch} &&
                echo '{patches_json}' | python /scripts/apply_patches.py &&
                git add -A &&
                git commit -m "Apply AI-generated patches" &&
                git push origin {branch} &&
                git rev-parse HEAD
                """
            ],
            environment={
                'GITHUB_TOKEN': os.environ['GITHUB_TOKEN']
            },
            mem_limit='2g',
            cpu_count=1,
            remove=True,
            timeout=300
        )
        
        output = container.decode('utf-8')
        commit_sha = output.strip().split('\n')[-1]
        
        return PatchResult(success=True, commit_sha=commit_sha)
```

### Dockerfile do Build Runner

```dockerfile
# Dockerfile.build-runner
FROM node:20-alpine

# Ferramentas de build
RUN apk add --no-cache git python3 bash

# Scripts de automação
COPY scripts/apply_patches.py /scripts/
COPY scripts/run_build.sh /scripts/

# Usuário não-root
RUN adduser -D builder
USER builder
WORKDIR /app

# Segurança: limitar capabilities
# (configurado no docker run)
```

---

## 4. AI Service

### Estrutura

```python
# services/ai_service.py
from abc import ABC, abstractmethod
from anthropic import Anthropic
from openai import OpenAI

class AIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass

class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str, model: str):
        self.client = Anthropic(api_key=api_key)
        self.model = model
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get('max_tokens', 4000),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

class AIService:
    def __init__(self, config: AIConfig):
        self.providers = {
            'content': self._create_provider(config.content_generation),
            'code': self._create_provider(config.code_generation),
            'analysis': self._create_provider(config.analysis)
        }
        self.prompts = load_prompts()
    
    async def generate(
        self, 
        task_type: str, 
        context: dict
    ) -> AIOutput:
        """Gera conteúdo usando prompt template"""
        
        # Selecionar provider
        if task_type in ['brief', 'sitemap', 'page_content']:
            provider = self.providers['content']
        elif task_type in ['layout_plan', 'code_patch', 'fix_build_error']:
            provider = self.providers['code']
        else:
            provider = self.providers['analysis']
        
        # Carregar e preencher prompt
        prompt_template = self.prompts[task_type]
        prompt = prompt_template.format(**context)
        
        # Chamar IA
        try:
            result = await provider.generate(prompt)
            
            # Validar output (JSON schema se aplicável)
            parsed = self._parse_and_validate(result, task_type)
            
            return AIOutput(
                success=True,
                artifact_type=task_type,
                content=parsed
            )
        except Exception as e:
            return AIOutput(
                success=False,
                error=str(e)
            )
```

---

## 5. Docker Compose (Produção)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # API Principal
  api:
    image: innexar/site-generator-api:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - postgres

  # Redis
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  # Postgres
  postgres:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=sitegen
      - POSTGRES_USER=sitegen
      - POSTGRES_PASSWORD=${DB_PASSWORD}

  # Worker Geral
  worker-general:
    image: innexar/site-generator-api:latest
    command: celery -A app.celery worker -Q general -c 4
    depends_on:
      - redis
      - postgres

  # Worker IA
  worker-ai:
    image: innexar/site-generator-api:latest
    command: celery -A app.celery worker -Q ai -c 2
    depends_on:
      - redis
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}

  # Worker Build
  worker-build:
    image: innexar/site-generator-api:latest
    command: celery -A app.celery worker -Q build -c 1
    depends_on:
      - redis
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Para criar containers
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}

volumes:
  redis_data:
  postgres_data:
```

---

*Última atualização: Janeiro 2026*
