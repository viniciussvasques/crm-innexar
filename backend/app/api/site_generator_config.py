from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from datetime import datetime
import logging
import sys
from app.core.database import get_db

logger = logging.getLogger(__name__)
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.configuration import (
    IntegrationConfigCreate, IntegrationConfigResponse, IntegrationConfigUpdate,
    DeployServerCreate, DeployServerResponse, DeployServerUpdate
)
from app.schemas.storage import StorageConfigCreate, StorageConfigResponse
from app.services.config_service import ConfigService
from app.models.configuration import IntegrationType, ServerType, DeployServer, IntegrationConfig

router = APIRouter()

# --- Integration Configs ---

@router.get("/config/integrations/{type}", response_model=List[IntegrationConfigResponse])
async def get_integrations_by_type(
    type: IntegrationType,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all configs for a specific integration type"""
    from app.services.config_service import ConfigService
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from app.core.config import settings
    
    result = await db.execute(
        select(IntegrationConfig).where(
            IntegrationConfig.integration_type == type,
            IntegrationConfig.is_active == True
        )
    )
    configs = result.scalars().all()
    
    # Decrypt secrets for display (frontend needs to see them to edit)
    sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    sync_engine = create_engine(sync_db_url)
    SyncSession = sessionmaker(bind=sync_engine)
    sync_db = SyncSession()
    
    try:
        service = ConfigService(sync_db)
        import sys
        msg = f"[GET INTEGRATIONS] Loading {len(configs)} configs for type: {type.value}"
        logger.info(msg)
        print(msg, file=sys.stderr, flush=True)
        for c in configs:
            if c.is_secret:
                # Decrypt for editing, but mask in response
                decrypted = service.decrypt_value(c.value)
                msg = f"[GET INTEGRATIONS] Decrypted {c.key}: {decrypted[:10]}... (length: {len(decrypted)})"
                logger.info(msg)
                print(msg, file=sys.stderr, flush=True)
                c.value = decrypted  # Return decrypted so frontend can edit
            else:
                msg = f"[GET INTEGRATIONS] Config {c.key}: {c.value}"
                logger.info(msg)
                print(msg, file=sys.stderr, flush=True)
    finally:
        sync_db.close()
        sync_engine.dispose()
    
    msg = f"[GET INTEGRATIONS] Returning {len(configs)} configs for {type.value}"
    logger.info(msg)
    print(msg, file=sys.stderr, flush=True)
    return configs

@router.post("/config/integrations", response_model=IntegrationConfigResponse)
async def create_integration_config(
    config: IntegrationConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update integration config"""
    from app.services.config_service import ConfigService
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from app.core.config import settings
    
    # Check if config already exists
    result = await db.execute(
        select(IntegrationConfig).where(
            IntegrationConfig.integration_type == config.integration_type,
            IntegrationConfig.key == config.key
        )
    )
    existing = result.scalar_one_or_none()
    
    # Create sync session for ConfigService encryption (temporary workaround)
    sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    sync_engine = create_engine(sync_db_url)
    SyncSession = sessionmaker(bind=sync_engine)
    sync_db = SyncSession()
    
    try:
        service = ConfigService(sync_db)
        
        # Encrypt if secret
        final_value = service.encrypt_value(config.value) if config.is_secret else config.value
        
        if existing:
            existing.value = final_value
            existing.is_secret = config.is_secret
            if config.description:
                existing.description = config.description
            existing.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            new_config = IntegrationConfig(
                integration_type=config.integration_type,
                key=config.key,
                value=final_value,
                is_secret=config.is_secret,
                description=config.description
            )
            db.add(new_config)
            await db.commit()
            await db.refresh(new_config)
            return new_config
    finally:
        sync_db.close()
        sync_engine.dispose()

@router.put("/config/integrations/{id}", response_model=IntegrationConfigResponse)
async def update_integration_config(
    id: int,
    config_update: IntegrationConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update integration config"""
    from app.services.config_service import ConfigService
    
    result = await db.execute(
        select(IntegrationConfig).where(IntegrationConfig.id == id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    # Create sync session for encryption
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from app.core.config import settings
    
    sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    sync_engine = create_engine(sync_db_url)
    SyncSession = sessionmaker(bind=sync_engine)
    sync_db = SyncSession()
    
    try:
        service = ConfigService(sync_db)
        
        if config_update.value is not None:
            if config.is_secret or config_update.is_secret:
                config.value = service.encrypt_value(config_update.value)
            else:
                config.value = config_update.value
    finally:
        sync_db.close()
        sync_engine.dispose()
            
    if config_update.is_secret is not None:
        config.is_secret = config_update.is_secret
    if config_update.description is not None:
        config.description = config_update.description
    if config_update.is_active is not None:
        config.is_active = config_update.is_active
        
    await db.commit()
    await db.refresh(config)
    return config

# --- Deploy Servers ---

@router.get("/config/deploy-servers", response_model=List[DeployServerResponse])
async def get_deploy_servers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(DeployServer).where(DeployServer.is_active == True)
    )
    return result.scalars().all()

@router.post("/config/deploy-servers", response_model=DeployServerResponse)
async def create_deploy_server(
    server: DeployServerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create deploy server"""
    from app.services.config_service import ConfigService
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from app.core.config import settings
    
    # Create sync session for encryption
    sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    sync_engine = create_engine(sync_db_url)
    SyncSession = sessionmaker(bind=sync_engine)
    sync_db = SyncSession()
    
    try:
        service = ConfigService(sync_db)
        
        # Encrypt sensitive fields
        password_encrypted = None
        ssh_key_encrypted = None
        if server.password:
            password_encrypted = service.encrypt_value(server.password)
        if server.ssh_key:
            ssh_key_encrypted = service.encrypt_value(server.ssh_key)
        
        new_server = DeployServer(
            name=server.name,
            server_type=server.server_type,
            host=server.host,
            port=server.port,
            username=server.username,
            deploy_path=server.deploy_path,
            is_default=server.is_default,
            password_encrypted=password_encrypted,
            ssh_key_encrypted=ssh_key_encrypted
        )
        db.add(new_server)
        await db.commit()
        await db.refresh(new_server)
        return new_server
    finally:
        sync_db.close()
        sync_engine.dispose()

# --- Storage Configuration (S3/R2) ---

@router.get("/config/storage", response_model=List[StorageConfigResponse])
async def get_storage_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all storage configurations"""
    result = await db.execute(
        select(IntegrationConfig).where(
            IntegrationConfig.integration_type.in_([IntegrationType.CLOUDFLARE_R2, IntegrationType.AWS_S3]),
            IntegrationConfig.is_active == True
        )
    )
    configs = result.scalars().all()
    
    # Group by provider and build response
    # This is simplified - in production, you'd want a proper StorageConfig model
    return []

@router.post("/config/storage", response_model=StorageConfigResponse)
async def create_storage_config(
    config: StorageConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create storage configuration"""
    from app.services.config_service import ConfigService
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from app.core.config import settings
    
    provider_type = IntegrationType.CLOUDFLARE_R2 if config.provider == "cloudflare_r2" else IntegrationType.AWS_S3
    
    # Create sync session for encryption
    sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    sync_engine = create_engine(sync_db_url)
    SyncSession = sessionmaker(bind=sync_engine)
    sync_db = SyncSession()
    
    try:
        service = ConfigService(sync_db)
        
        # Helper to set config async
        async def set_config_async(key: str, value: str, is_secret: bool):
            result = await db.execute(
                select(IntegrationConfig).where(
                    IntegrationConfig.integration_type == provider_type,
                    IntegrationConfig.key == key
                )
            )
            existing = result.scalar_one_or_none()
            
            final_value = service.encrypt_value(value) if is_secret else value
            
            if existing:
                existing.value = final_value
                existing.updated_at = datetime.utcnow()
            else:
                new_config = IntegrationConfig(
                    integration_type=provider_type,
                    key=key,
                    value=final_value,
                    is_secret=is_secret
                )
                db.add(new_config)
        
        await set_config_async("bucket_name", config.bucket_name, False)
        await set_config_async("access_key_id", config.access_key_id, True)
        await set_config_async("secret_access_key", config.secret_access_key, True)
        if config.endpoint_url:
            await set_config_async("endpoint_url", config.endpoint_url, False)
        if config.region:
            await set_config_async("region", config.region, False)
        
        await db.commit()
    finally:
        sync_db.close()
        sync_engine.dispose()
    
    # Return simplified response
    return StorageConfigResponse(
        id=1,  # Would be actual ID in production
        provider=config.provider,
        bucket_name=config.bucket_name,
        access_key_id="********",
        endpoint_url=config.endpoint_url,
        region=config.region,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@router.post("/config/storage/test")
async def test_storage_connection(
    provider: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test storage connection"""
    logger.info(f"🧪 [STORAGE TEST] Starting test for provider: {provider} (user: {current_user.email})")
    print(f"🧪 [STORAGE TEST] Starting test for provider: {provider} (user: {current_user.email})")
    
    from app.services.config_service import ConfigService
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from app.core.config import settings
    import httpx
    
    provider_type = IntegrationType.CLOUDFLARE_R2 if provider == "cloudflare_r2" else IntegrationType.AWS_S3
    logger.info(f"🧪 [STORAGE TEST] Provider type: {provider_type.value}")
    
    # Get config
    sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    sync_engine = create_engine(sync_db_url)
    SyncSession = sessionmaker(bind=sync_engine)
    sync_db = SyncSession()
    
    try:
        service = ConfigService(sync_db)
        
        result = await db.execute(
            select(IntegrationConfig).where(
                IntegrationConfig.integration_type == provider_type,
                IntegrationConfig.is_active == True
            )
        )
        configs = {c.key: service.decrypt_value(c.value) if c.is_secret else c.value for c in result.scalars().all()}
        logger.info(f"🧪 [STORAGE TEST] Found {len(configs)} config keys: {list(configs.keys())}")
        
        bucket = configs.get("bucket_name")
        access_key = configs.get("access_key_id")
        secret_key = configs.get("secret_access_key")
        endpoint = configs.get("endpoint_url")
        region = configs.get("region", "auto")
        
        if not all([bucket, access_key, secret_key]):
            msg = f"Missing required configuration. Bucket: {bool(bucket)}, Access Key: {bool(access_key)}, Secret Key: {bool(secret_key)}"
            logger.warning(f"🧪 [STORAGE TEST] {msg}")
            print(f"🧪 [STORAGE TEST] {msg}", file=sys.stderr, flush=True)
            return {"success": False, "error": f"Missing required configuration for {provider}. Please configure {provider} first."}
        
        logger.info(f"🧪 [STORAGE TEST] Testing connection to bucket: {bucket}")
        
        # Test R2 (S3-compatible)
        if provider == "cloudflare_r2":
            import boto3
            from botocore.exceptions import ClientError
            
            endpoint_url = endpoint or f"https://{access_key[:8]}.r2.cloudflarestorage.com"
            logger.info(f"🧪 [STORAGE TEST] Using R2 endpoint: {endpoint_url}")
            
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region or "auto"
            )
            
            try:
                logger.info(f"🧪 [STORAGE TEST] Attempting head_bucket for bucket: {bucket}")
                print(f"🧪 [STORAGE TEST] Attempting head_bucket for bucket: {bucket}", file=sys.stderr, flush=True)
                s3_client.head_bucket(Bucket=bucket)
                logger.info(f"✅ [STORAGE TEST] Successfully connected to R2 bucket '{bucket}'")
                print(f"✅ [STORAGE TEST] Successfully connected to R2 bucket '{bucket}'", file=sys.stderr, flush=True)
                return {"success": True, "message": f"Successfully connected to R2 bucket '{bucket}'"}
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_msg = str(e)
                logger.error(f"❌ [STORAGE TEST] Failed to connect to R2: {error_code} - {error_msg}")
                print(f"❌ [STORAGE TEST] Failed to connect to R2: {error_code} - {error_msg}", file=sys.stderr, flush=True)
                
                if error_code == '404' or 'Not Found' in error_msg:
                    return {"success": False, "error": f"Bucket '{bucket}' not found. Please create the bucket in Cloudflare R2 first or check the bucket name."}
                elif error_code == '403' or 'Forbidden' in error_msg:
                    return {"success": False, "error": f"Access denied to bucket '{bucket}'. Please check your R2 credentials and permissions."}
                else:
                    return {"success": False, "error": f"Failed to connect: {error_code} - {error_msg}"}
        
        # Test AWS S3
        elif provider == "aws_s3":
            import boto3
            from botocore.exceptions import ClientError
            
            logger.info(f"🧪 [STORAGE TEST] Using AWS S3 region: {region or 'us-east-1'}")
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region or "us-east-1"
            )
            
            try:
                logger.info(f"🧪 [STORAGE TEST] Attempting head_bucket for bucket: {bucket}")
                s3_client.head_bucket(Bucket=bucket)
                logger.info(f"✅ [STORAGE TEST] Successfully connected to S3 bucket '{bucket}'")
                return {"success": True, "message": f"Successfully connected to S3 bucket '{bucket}'"}
            except ClientError as e:
                error_msg = str(e)
                logger.error(f"❌ [STORAGE TEST] Failed to connect to S3: {error_msg}")
                return {"success": False, "error": f"Failed to connect: {error_msg}"}
        
        logger.warning(f"🧪 [STORAGE TEST] Unknown provider: {provider}")
        return {"success": False, "error": "Unknown provider"}
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"❌ [STORAGE TEST] Exception during test: {error_msg}")
        return {"success": False, "error": f"Test failed: {error_msg}"}
    finally:
        sync_db.close()
        sync_engine.dispose()

# --- Cloudflare Pages Configuration ---

@router.post("/config/cloudflare-pages")
async def configure_cloudflare_pages(
    account_id: str,
    api_token: str,
    project_template: str = "site-{order_id}",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Configure Cloudflare Pages"""
    from app.services.config_service import ConfigService
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from app.core.config import settings
    
    # Create sync session for encryption
    sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    sync_engine = create_engine(sync_db_url)
    SyncSession = sessionmaker(bind=sync_engine)
    sync_db = SyncSession()
    
    try:
        service = ConfigService(sync_db)
        
        # Helper to set config async
        async def set_config_async(key: str, value: str, is_secret: bool):
            result = await db.execute(
                select(IntegrationConfig).where(
                    IntegrationConfig.integration_type == IntegrationType.CLOUDFLARE_PAGES,
                    IntegrationConfig.key == key
                )
            )
            existing = result.scalar_one_or_none()
            
            final_value = service.encrypt_value(value) if is_secret else value
            
            if existing:
                existing.value = final_value
                existing.updated_at = datetime.utcnow()
            else:
                new_config = IntegrationConfig(
                    integration_type=IntegrationType.CLOUDFLARE_PAGES,
                    key=key,
                    value=final_value,
                    is_secret=is_secret
                )
                db.add(new_config)
        
        await set_config_async("account_id", account_id, False)
        await set_config_async("api_token", api_token, True)
        await set_config_async("project_template", project_template, False)
        
        await db.commit()
    finally:
        sync_db.close()
        sync_engine.dispose()
    
    return {"success": True, "message": "Cloudflare Pages configured"}

@router.post("/config/cloudflare-pages/test")
async def test_cloudflare_pages(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test Cloudflare Pages connection"""
    logger.info(f"🧪 [CLOUDFLARE PAGES TEST] Starting test (user: {current_user.email})")
    print(f"🧪 [CLOUDFLARE PAGES TEST] Starting test (user: {current_user.email})")
    
    from app.services.config_service import ConfigService
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from app.core.config import settings
    import httpx
    
    # Get config
    sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    sync_engine = create_engine(sync_db_url)
    SyncSession = sessionmaker(bind=sync_engine)
    sync_db = SyncSession()
    
    try:
        service = ConfigService(sync_db)
        
        # Get Pages-specific config
        result = await db.execute(
            select(IntegrationConfig).where(
                IntegrationConfig.integration_type == IntegrationType.CLOUDFLARE_PAGES,
                IntegrationConfig.is_active == True
            )
        )
        pages_configs = {c.key: service.decrypt_value(c.value) if c.is_secret else c.value for c in result.scalars().all()}
        
        # Get base Cloudflare config (token and account_id are stored there)
        base_result = await db.execute(
            select(IntegrationConfig).where(
                IntegrationConfig.integration_type == IntegrationType.CLOUDFLARE,
                IntegrationConfig.is_active == True
            )
        )
        base_configs = {c.key: service.decrypt_value(c.value) if c.is_secret else c.value for c in base_result.scalars().all()}
        
        logger.info(f"🧪 [CLOUDFLARE PAGES TEST] Found {len(pages_configs)} Pages configs, {len(base_configs)} base configs")
        print(f"🧪 [CLOUDFLARE PAGES TEST] Found {len(pages_configs)} Pages configs, {len(base_configs)} base configs", file=sys.stderr, flush=True)
        
        api_token = base_configs.get("api_token")
        account_id = base_configs.get("account_id")
        
        if not api_token or not account_id:
            msg = f"Missing configuration. Token: {bool(api_token)}, Account ID: {bool(account_id)}"
            logger.warning(f"🧪 [CLOUDFLARE PAGES TEST] {msg}")
            print(f"🧪 [CLOUDFLARE PAGES TEST] {msg}", file=sys.stderr, flush=True)
            return {"success": False, "error": "Missing API token or Account ID. Please configure Cloudflare Base first."}
        
        logger.info(f"🧪 [CLOUDFLARE PAGES TEST] Testing API connection for account: {account_id}")
        
        # Test Cloudflare Pages API
        async with httpx.AsyncClient() as client:
            url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects"
            logger.info(f"🧪 [CLOUDFLARE PAGES TEST] Calling: {url}")
            
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )
            
            logger.info(f"🧪 [CLOUDFLARE PAGES TEST] Response status: {response.status_code}")
            print(f"🧪 [CLOUDFLARE PAGES TEST] Response status: {response.status_code}", file=sys.stderr, flush=True)
            
            if response.status_code == 200:
                projects = response.json().get("result", [])
                logger.info(f"✅ [CLOUDFLARE PAGES TEST] Successfully connected. Found {len(projects)} projects")
                print(f"✅ [CLOUDFLARE PAGES TEST] Successfully connected. Found {len(projects)} projects", file=sys.stderr, flush=True)
                return {"success": True, "message": f"Successfully connected to Cloudflare Pages API (found {len(projects)} projects)"}
            elif response.status_code == 403:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("errors", [{}])[0].get("message", "Authentication error")
                logger.error(f"❌ [CLOUDFLARE PAGES TEST] Authentication error: {error_msg}")
                print(f"❌ [CLOUDFLARE PAGES TEST] Authentication error: {error_msg}", file=sys.stderr, flush=True)
                return {"success": False, "error": f"Authentication failed: {error_msg}. Please check if your API token has 'Pages Write' permission."}
            else:
                error_text = response.text[:200]
                logger.error(f"❌ [CLOUDFLARE PAGES TEST] API error {response.status_code}: {error_text}")
                print(f"❌ [CLOUDFLARE PAGES TEST] API error {response.status_code}: {error_text}", file=sys.stderr, flush=True)
                return {"success": False, "error": f"API returned {response.status_code}: {error_text}"}
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"❌ [CLOUDFLARE PAGES TEST] Exception: {error_msg}")
        return {"success": False, "error": f"Test failed: {error_msg}"}
    finally:
        sync_db.close()
        sync_engine.dispose()

@router.post("/config/integrations/{type}/test")
async def test_integration(
    type: IntegrationType,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test integration connection"""
    logger.info(f"🧪 [INTEGRATION TEST] Starting test for type: {type.value} (user: {current_user.email})")
    print(f"🧪 [INTEGRATION TEST] Starting test for type: {type.value} (user: {current_user.email})")
    
    from app.services.config_service import ConfigService
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from app.core.config import settings
    import httpx
    
    # Get config
    sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    sync_engine = create_engine(sync_db_url)
    SyncSession = sessionmaker(bind=sync_engine)
    sync_db = SyncSession()
    
    try:
        service = ConfigService(sync_db)
        
        result = await db.execute(
            select(IntegrationConfig).where(
                IntegrationConfig.integration_type == type,
                IntegrationConfig.is_active == True
            )
        )
        configs = {c.key: service.decrypt_value(c.value) if c.is_secret else c.value for c in result.scalars().all()}
        logger.info(f"🧪 [INTEGRATION TEST] Found {len(configs)} config keys: {list(configs.keys())}")
        
        # Test GitHub
        if type == IntegrationType.GITHUB:
            logger.info("🧪 [INTEGRATION TEST] Testing GitHub API")
            api_token = configs.get("api_token")
            if not api_token:
                logger.warning("🧪 [INTEGRATION TEST] Missing GitHub API token")
                return {"success": False, "error": "Missing GitHub API token"}
            
            async with httpx.AsyncClient() as client:
                logger.info("🧪 [INTEGRATION TEST] Calling GitHub API: https://api.github.com/user")
                response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"token {api_token}",
                        "Accept": "application/vnd.github.v3+json"
                    },
                    timeout=10.0
                )
                
                logger.info(f"🧪 [INTEGRATION TEST] GitHub response status: {response.status_code}")
                
                if response.status_code == 200:
                    user_data = response.json()
                    username = user_data.get('login', 'user')
                    logger.info(f"✅ [INTEGRATION TEST] GitHub connected as: {username}")
                    return {"success": True, "message": f"Connected as {username}"}
                else:
                    error_text = response.text[:200]
                    logger.error(f"❌ [INTEGRATION TEST] GitHub API error {response.status_code}: {error_text}")
                    return {"success": False, "error": f"API returned {response.status_code}: {error_text}"}
        
        # Test Cloudflare Base
        elif type == IntegrationType.CLOUDFLARE:
            logger.info("🧪 [INTEGRATION TEST] Testing Cloudflare Base API")
            api_token = configs.get("api_token")
            account_id = configs.get("account_id")
            
            if not api_token or not account_id:
                logger.warning(f"🧪 [INTEGRATION TEST] Missing configuration. Token: {bool(api_token)}, Account ID: {bool(account_id)}")
                return {"success": False, "error": "Missing API token or Account ID"}
            
            async with httpx.AsyncClient() as client:
                url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}"
                logger.info(f"🧪 [INTEGRATION TEST] Calling: {url}")
                response = await client.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {api_token}",
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )
                
                logger.info(f"🧪 [INTEGRATION TEST] Cloudflare response status: {response.status_code}")
                
                if response.status_code == 200:
                    account_data = response.json()
                    account_name = account_data.get("result", {}).get("name", "account")
                    logger.info(f"✅ [INTEGRATION TEST] Cloudflare connected to account: {account_name}")
                    return {"success": True, "message": f"Successfully connected to Cloudflare API (account: {account_name})"}
                else:
                    error_text = response.text[:200]
                    logger.error(f"❌ [INTEGRATION TEST] Cloudflare API error {response.status_code}: {error_text}")
                    return {"success": False, "error": f"API returned {response.status_code}: {error_text}"}
        
        # Test Cloudflare DNS
        elif type == IntegrationType.CLOUDFLARE_DNS:
            logger.info("🧪 [INTEGRATION TEST] Testing Cloudflare DNS API")
            # Get token from base cloudflare config
            base_result = await db.execute(
                select(IntegrationConfig).where(
                    IntegrationConfig.integration_type == IntegrationType.CLOUDFLARE,
                    IntegrationConfig.key == "api_token",
                    IntegrationConfig.is_active == True
                )
            )
            base_token = None
            base_config = base_result.scalar_one_or_none()
            if base_config:
                base_token = service.decrypt_value(base_config.value) if base_config.is_secret else base_config.value
            
            zone_id = configs.get("zone_id")
            
            if not base_token or not zone_id:
                logger.warning(f"🧪 [INTEGRATION TEST] Missing configuration. Token: {bool(base_token)}, Zone ID: {bool(zone_id)}")
                return {"success": False, "error": "Missing API token or Zone ID"}
            
            async with httpx.AsyncClient() as client:
                url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}"
                logger.info(f"🧪 [INTEGRATION TEST] Calling: {url}")
                response = await client.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {base_token}",
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )
                
                logger.info(f"🧪 [INTEGRATION TEST] Cloudflare DNS response status: {response.status_code}")
                
                if response.status_code == 200:
                    zone_data = response.json()
                    zone_name = zone_data.get("result", {}).get("name", "zone")
                    logger.info(f"✅ [INTEGRATION TEST] Cloudflare DNS connected to zone: {zone_name}")
                    return {"success": True, "message": f"Successfully connected to DNS zone '{zone_name}'"}
                else:
                    error_text = response.text[:200]
                    logger.error(f"❌ [INTEGRATION TEST] Cloudflare DNS API error {response.status_code}: {error_text}")
                    return {"success": False, "error": f"API returned {response.status_code}: {error_text}"}
        
        logger.warning(f"🧪 [INTEGRATION TEST] Integration type not supported: {type.value}")
        return {"success": False, "error": "Integration type not supported for testing"}
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"❌ [INTEGRATION TEST] Exception for {type.value}: {error_msg}")
        return {"success": False, "error": f"Test failed: {error_msg}"}
    finally:
        sync_db.close()
        sync_engine.dispose()
