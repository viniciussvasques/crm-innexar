"""
Cloudflare DNS Service
Handles DNS record management for subdomains
"""
import httpx
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.services.config_service import ConfigService
from app.models.configuration import IntegrationType

logger = logging.getLogger(__name__)


class CloudflareDNSService:
    def __init__(self, db: Session):
        self.db = db
        self.config_service = ConfigService(db)
        self._api_token = None
        self._zone_id = None
        
    def _load_config(self):
        """Load Cloudflare DNS configuration"""
        if self._api_token and self._zone_id:
            return
            
        # Get base Cloudflare config (for API token)
        base_configs = self.config_service.get_all_by_type(IntegrationType.CLOUDFLARE)
        self._api_token = base_configs.get("api_token")
        
        # Get DNS-specific config
        dns_configs = self.config_service.get_all_by_type(IntegrationType.CLOUDFLARE_DNS)
        self._zone_id = dns_configs.get("zone_id")
        
        if not self._api_token:
            raise ValueError("Cloudflare API token not configured")
        if not self._zone_id:
            raise ValueError("Cloudflare Zone ID not configured for DNS")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API headers"""
        return {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json"
        }
    
    async def create_subdomain(self, subdomain: str, target: str, record_type: str = "CNAME") -> Dict[str, Any]:
        """
        Create a DNS record (subdomain)
        
        Args:
            subdomain: Subdomain name (e.g., "site-24" for site-24.example.com)
            target: Target value (e.g., "site-24.pages.dev" for CNAME)
            record_type: DNS record type (default: CNAME)
            
        Returns:
            Dict with DNS record information
        """
        self._load_config()
        
        async with httpx.AsyncClient() as client:
            url = f"https://api.cloudflare.com/client/v4/zones/{self._zone_id}/dns_records"
            
            payload = {
                "type": record_type,
                "name": subdomain,
                "content": target,
                "ttl": 1  # Automatic TTL
            }
            
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                record = result.get("result", {})
                logger.info(f"✅ Created DNS record: {subdomain} -> {target}")
                return {
                    "success": True,
                    "record": record,
                    "name": record.get("name"),
                    "content": record.get("content"),
                    "type": record.get("type")
                }
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                errors = error_data.get("errors", [])
                error_msg = errors[0].get("message", "Unknown error") if errors else response.text
                logger.error(f"❌ Failed to create DNS record {subdomain}: {error_msg}")
                raise Exception(f"Failed to create DNS record: {error_msg}")
    
    async def get_record(self, subdomain: str, record_type: str = "CNAME") -> Optional[Dict[str, Any]]:
        """Get DNS record by name"""
        self._load_config()
        
        async with httpx.AsyncClient() as client:
            url = f"https://api.cloudflare.com/client/v4/zones/{self._zone_id}/dns_records"
            params = {
                "name": subdomain,
                "type": record_type
            }
            
            response = await client.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                records = result.get("result", [])
                return records[0] if records else None
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                errors = error_data.get("errors", [])
                error_msg = errors[0].get("message", "Unknown error") if errors else response.text
                raise Exception(f"Failed to get DNS record: {error_msg}")
    
    async def update_record(self, record_id: str, subdomain: str, target: str, record_type: str = "CNAME") -> Dict[str, Any]:
        """Update an existing DNS record"""
        self._load_config()
        
        async with httpx.AsyncClient() as client:
            url = f"https://api.cloudflare.com/client/v4/zones/{self._zone_id}/dns_records/{record_id}"
            
            payload = {
                "type": record_type,
                "name": subdomain,
                "content": target,
                "ttl": 1
            }
            
            response = await client.put(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                record = result.get("result", {})
                logger.info(f"✅ Updated DNS record: {subdomain} -> {target}")
                return {
                    "success": True,
                    "record": record
                }
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                errors = error_data.get("errors", [])
                error_msg = errors[0].get("message", "Unknown error") if errors else response.text
                logger.error(f"❌ Failed to update DNS record {subdomain}: {error_msg}")
                raise Exception(f"Failed to update DNS record: {error_msg}")
    
    async def delete_record(self, record_id: str) -> bool:
        """Delete a DNS record"""
        self._load_config()
        
        async with httpx.AsyncClient() as client:
            url = f"https://api.cloudflare.com/client/v4/zones/{self._zone_id}/dns_records/{record_id}"
            
            response = await client.delete(
                url,
                headers=self._get_headers(),
                timeout=10.0
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Deleted DNS record: {record_id}")
                return True
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                errors = error_data.get("errors", [])
                error_msg = errors[0].get("message", "Unknown error") if errors else response.text
                logger.error(f"❌ Failed to delete DNS record {record_id}: {error_msg}")
                raise Exception(f"Failed to delete DNS record: {error_msg}")
    
    async def list_records(self, record_type: str = None) -> List[Dict[str, Any]]:
        """List all DNS records in the zone"""
        self._load_config()
        
        async with httpx.AsyncClient() as client:
            url = f"https://api.cloudflare.com/client/v4/zones/{self._zone_id}/dns_records"
            params = {}
            if record_type:
                params["type"] = record_type
            
            response = await client.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("result", [])
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                errors = error_data.get("errors", [])
                error_msg = errors[0].get("message", "Unknown error") if errors else response.text
                raise Exception(f"Failed to list DNS records: {error_msg}")
