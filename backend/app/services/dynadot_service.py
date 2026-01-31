"""
Dynadot Domain Service
Handles domain availability checking and registration via Dynadot API
"""
import httpx
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)


class DynadotService:
    def __init__(self, db: AsyncSession = None):
        self.db = db
        self.api_key = None
        self.api_secret = None
        self.max_domain_price = None
        self.base_url = "https://api.dynadot.com/api3.json"

    async def _load_config(self):
        """Load Dynadot configuration from database."""
        if not self.db:
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                await self._load_from_session(session)
        else:
            await self._load_from_session(self.db)

    async def _load_from_session(self, session: AsyncSession):
        """Load configuration from database session."""
        result = await session.execute(
            select(SystemConfig).where(
                SystemConfig.key.in_([
                    "dynadot_api_key",
                    "dynadot_api_secret",
                    "dynadot_max_domain_price"
                ])
            )
        )
        configs = {row.key: row for row in result.scalars().all()}
        
        # Get and strip whitespace from API key (common issue when copying/pasting)
        api_key_config = configs.get("dynadot_api_key")
        if api_key_config and api_key_config.value:
            self.api_key = api_key_config.value.strip()
            logger.info(f"[Dynadot] Loaded API key (length: {len(self.api_key)}): {self.api_key[:8]}...{self.api_key[-4:] if len(self.api_key) > 12 else ''}")
        else:
            self.api_key = None
            logger.warning("[Dynadot] API key not found in database")
        
        # Get and strip whitespace from API secret
        api_secret_config = configs.get("dynadot_api_secret")
        if api_secret_config and api_secret_config.value:
            self.api_secret = api_secret_config.value.strip()
        else:
            self.api_secret = None
        
        max_price_str = configs.get("dynadot_max_domain_price").value if configs.get("dynadot_max_domain_price") else "15.00"
        try:
            self.max_domain_price = float(max_price_str)
        except (ValueError, TypeError):
            self.max_domain_price = 15.00

    async def check_domain_availability(self, domain: str) -> Dict[str, Any]:
        """
        Check if a domain is available for registration.
        
        Args:
            domain: Domain name to check (e.g., "example.com")
            
        Returns:
            Dict with availability status, price, and other info
        """
        await self._load_config()
        
        if not self.api_key:
            raise ValueError("Dynadot API Key not configured")
        
        # Clean domain name (remove protocol, www, etc.)
        domain = domain.lower().strip()
        domain = domain.replace("http://", "").replace("https://", "").replace("www.", "")
        domain = domain.split("/")[0]  # Remove paths
        
        if "." not in domain and domain != "localhost":
             return {
                "available": False,
                "error": "Invalid domain format: missing extension (e.g. .com)",
                "domain": domain
            }
        
        logger.info(f"[Dynadot] Checking domain availability for: {domain}")
        logger.info(f"[Dynadot] Using API key: {self.api_key[:10]}...{self.api_key[-4:] if len(self.api_key) > 14 else '****'}")
        
        try:
            # Increased timeout to 30s to allow Dynadot API to respond
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Dynadot API uses POST with form data
                # Ensure API key has no whitespace (already stripped in _load_from_session, but double-check)
                clean_api_key = self.api_key.strip() if self.api_key else None
                if not clean_api_key:
                    raise ValueError("Dynadot API Key is empty after cleaning")
                
                params = {
                    "key": clean_api_key,
                    "command": "search",
                    "domain0": domain
                }
                
                if self.api_secret:
                    params["secret"] = self.api_secret.strip()  # Ensure no whitespace
                
                logger.info(f"[Dynadot] Request params: key={clean_api_key[:8]}...{clean_api_key[-4:] if len(clean_api_key) > 12 else ''}, command={params['command']}, domain={params['domain0']}")
                
                response = await client.get(
                    self.base_url,
                    params=params
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Dynadot API error: {response.status_code} - {error_text}")
                    return {
                        "available": False,
                        "error": f"API returned status {response.status_code}",
                        "domain": domain
                    }
                
                try:
                    data = response.json()
                    logger.info(f"[Dynadot] Parsed JSON response: {data}")
                except Exception as json_error:
                    logger.error(f"Error parsing Dynadot JSON response: {json_error}, Response text: {response.text[:200]}")
                    return {
                        "available": False,
                        "error": f"Invalid response from Dynadot API: {str(json_error)}",
                        "domain": domain
                    }
                
                # Parse Dynadot response
                # Success format: {"SearchResponse": {"SearchStatus": {"domain0": {"result": "yes", "price": "12.99"}}}}
                # Error format: {"Response": {"ResponseCode": "-1", "Error": "error message"}}
                
                # Check for error response first
                error_response = data.get("Response", {})
                if error_response:
                    response_code = error_response.get("ResponseCode", "")
                    error_message = error_response.get("Error", "Unknown error from Dynadot API")
                    
                    # ResponseCode "0" means success, anything else is an error
                    if response_code and response_code != "0":
                        logger.error(f"[Dynadot] API error for domain {domain}: {error_message} (Code: {response_code})")
                        return {
                            "available": False,
                            "error": f"Dynadot API error: {error_message}",
                            "domain": domain,
                            "raw_response": data
                        }
                    # If ResponseCode is "0" but there's an Error field, still treat as error
                    if error_message and error_message != "Unknown error from Dynadot API":
                        logger.error(f"[Dynadot] API error for domain {domain}: {error_message}")
                        return {
                            "available": False,
                            "error": f"Dynadot API error: {error_message}",
                            "domain": domain,
                            "raw_response": data
                        }
                
                search_response = data.get("SearchResponse", {})
                if not search_response:
                    logger.warning(f"Unexpected Dynadot response format: {data}")
                    return {
                        "available": False,
                        "error": "Unexpected response format from Dynadot API",
                        "domain": domain,
                        "raw_response": data
                    }
                
                search_status = search_response.get("SearchStatus", {})
                domain_info = search_status.get("domain0", {})
                
                if not domain_info:
                    # Check for SearchResults (newer API format)
                    search_results = search_response.get("SearchResults")
                    if search_results and isinstance(search_results, list) and len(search_results) > 0:
                        first_result = search_results[0]
                        
                        # Check for error first
                        if first_result.get("Status") == "error":
                            error_msg = first_result.get("Error", "Unknown validation error")
                            logger.error(f"[Dynadot] Validation error for domain {domain}: {error_msg}")
                            return {
                                "available": False,
                                "error": f"Dynadot error: {error_msg}",
                                "domain": domain,
                                "raw_response": data
                            }
                            
                        # Parse success response from SearchResults
                        status = first_result.get("Status")
                        if status == "success":
                            available_str = first_result.get("Available", "no").lower()
                            price_str = first_result.get("Price", "0")
                            
                            try:
                                price = float(price_str)
                            except (ValueError, TypeError):
                                price = 0.0
                                
                            available = available_str == "yes"
                            is_free = available and price <= self.max_domain_price
                            
                            logger.info(f"[Dynadot] Domain {domain} (from SearchResults): available={available}, price={price}, is_free={is_free}")
                            
                            return {
                                "available": available,
                                "domain": domain,
                                "price": price,
                                "is_free": is_free,
                                "max_free_price": self.max_domain_price,
                                "result": available_str,
                                "raw_response": first_result
                            }

                    logger.warning(f"No domain info in response: {data}")
                    return {
                        "available": False,
                        "error": "No domain information in API response",
                        "domain": domain,
                        "raw_response": data
                    }
                
                result = domain_info.get("result", "").lower()
                price_str = domain_info.get("price", "0")
                
                try:
                    price = float(price_str)
                except (ValueError, TypeError):
                    price = 0.0
                
                # Determine availability
                available = result == "yes"
                is_free = available and price <= self.max_domain_price
                
                logger.info(f"[Dynadot] Domain {domain}: available={available}, price={price}, is_free={is_free}")
                
                return {
                    "available": available,
                    "domain": domain,
                    "price": price,
                    "is_free": is_free,
                    "max_free_price": self.max_domain_price,
                    "result": result,
                    "raw_response": domain_info
                }
                
        except httpx.TimeoutException:
            logger.error(f"Dynadot API timeout for domain {domain}")
            return {
                "available": False,
                "error": "API timeout - please try again",
                "domain": domain
            }
        except httpx.RequestError as e:
            logger.error(f"Dynadot API request error for domain {domain}: {e}")
            return {
                "available": False,
                "error": f"Connection error: {str(e)}",
                "domain": domain
            }
        except Exception as e:
            logger.error(f"Error checking domain availability for {domain}: {e}", exc_info=True)
            return {
                "available": False,
                "error": str(e),
                "domain": domain
            }

    async def check_multiple_domains(self, domains: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Check availability for multiple domains (up to 100 per API call).
        
        Args:
            domains: List of domain names to check
            
        Returns:
            Dict mapping domain -> availability info
        """
        await self._load_config()
        
        if not self.api_key:
            raise ValueError("Dynadot API Key not configured")
        
        # Clean domains
        cleaned_domains = []
        for domain in domains:
            domain = domain.lower().strip()
            domain = domain.replace("http://", "").replace("https://", "").replace("www.", "")
            domain = domain.split("/")[0]
            cleaned_domains.append(domain)
        
        # Dynadot allows up to 100 domains per call
        results = {}
        batch_size = 100
        
        for i in range(0, len(cleaned_domains), batch_size):
            batch = cleaned_domains[i:i + batch_size]
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    params = {
                        "key": self.api_key,
                        "command": "search"
                    }
                    
                    if self.api_secret:
                        params["secret"] = self.api_secret
                    
                    # Add domains as domain0, domain1, etc.
                    for idx, domain in enumerate(batch):
                        params[f"domain{idx}"] = domain
                    
                    response = await client.get(
                        self.base_url,
                        params=params
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        search_response = data.get("SearchResponse", {})
                        search_status = search_response.get("SearchStatus", {})
                        
                        # Check for SearchStatus (old format)
                        if search_status:
                            for idx, domain in enumerate(batch):
                                domain_key = f"domain{idx}"
                                domain_info = search_status.get(domain_key, {})
                                
                                result = domain_info.get("result", "").lower()
                                price_str = domain_info.get("price", "0")
                                
                                try:
                                    price = float(price_str)
                                except (ValueError, TypeError):
                                    price = 0.0
                                
                                available = result == "yes"
                                is_free = available and price <= self.max_domain_price
                                
                                results[domain] = {
                                    "available": available,
                                    "domain": domain,
                                    "price": price,
                                    "is_free": is_free,
                                    "max_free_price": self.max_domain_price,
                                    "result": result,
                                    "raw_response": domain_info
                                }
                        # Check for SearchResults (new format)
                        elif "SearchResults" in search_response:
                            search_results = search_response.get("SearchResults", [])
                            # Map results by domain name
                            results_map = {item.get("DomainName"): item for item in search_results if item.get("DomainName")}
                            
                            for domain in batch:
                                item = results_map.get(domain, {})
                                if item:
                                    status = item.get("Status")
                                    if status == "error":
                                        results[domain] = {
                                            "available": False,
                                            "error": item.get("Error", "Unknown error"),
                                            "domain": domain
                                        }
                                    else:
                                        available_str = item.get("Available", "no").lower()
                                        price_str = item.get("Price", "0")
                                        
                                        try:
                                            price = float(price_str)
                                        except (ValueError, TypeError):
                                            price = 0.0
                                            
                                        available = available_str == "yes"
                                        is_free = available and price <= self.max_domain_price
                                        
                                        results[domain] = {
                                            "available": available,
                                            "domain": domain,
                                            "price": price,
                                            "is_free": is_free,
                                            "max_free_price": self.max_domain_price,
                                            "result": available_str,
                                            "raw_response": item
                                        }
                                else:
                                    results[domain] = {
                                        "available": False,
                                        "error": "No data for domain",
                                        "domain": domain
                                    }
                        else:
                            # No recognizable data
                             for domain in batch:
                                results[domain] = {
                                    "available": False,
                                    "error": "Invalid API response format",
                                    "domain": domain
                                }
                    else:
                        # If batch fails, mark all as error
                        for domain in batch:
                            results[domain] = {
                                "available": False,
                                "error": f"API returned status {response.status_code}",
                                "domain": domain
                            }
                            
            except Exception as e:
                logger.error(f"Error checking batch of domains: {e}")
                for domain in batch:
                    results[domain] = {
                        "available": False,
                        "error": str(e),
                        "domain": domain
                    }
        
        return results

    async def get_domain_price(self, domain: str) -> Optional[float]:
        """
        Get the registration price for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            Price in USD, or None if unavailable
        """
        result = await self.check_domain_availability(domain)
        if result.get("available"):
            return result.get("price")
        return None

    async def register_domain(self, domain: str, duration_years: int = 1) -> Dict[str, Any]:
        """
        Register/purchase a domain via Dynadot API.
        
        Args:
            domain: Domain name to register
            duration_years: Registration duration in years (default: 1)
            
        Returns:
            Dict with registration result
        """
        await self._load_config()
        
        if not self.api_key:
            raise ValueError("Dynadot API Key not configured")
        
        # Clean domain name
        domain = domain.lower().strip()
        domain = domain.replace("http://", "").replace("https://", "").replace("www.", "")
        domain = domain.split("/")[0]
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                params = {
                    "key": self.api_key,
                    "command": "register",
                    "domain": domain,
                    "duration": str(duration_years)
                }
                
                if self.api_secret:
                    params["secret"] = self.api_secret
                
                response = await client.get(
                    self.base_url,
                    params=params
                )
                
                if response.status_code != 200:
                    logger.error(f"Dynadot API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API returned status {response.status_code}",
                        "domain": domain
                    }
                
                data = response.json()
                
                # Parse Dynadot response
                # Response format: {"RegisterResponse": {"RegisterStatus": {"domain": "example.com", "result": "success", "expiration_date": "..."}}}
                register_response = data.get("RegisterResponse", {})
                register_status = register_response.get("RegisterStatus", {})
                
                result = register_status.get("result", "").lower()
                expiration_date = register_status.get("expiration_date")
                
                success = result == "success"
                
                return {
                    "success": success,
                    "domain": domain,
                    "result": result,
                    "expiration_date": expiration_date,
                    "raw_response": register_status
                }
                
        except httpx.TimeoutException:
            logger.error(f"Dynadot API timeout for domain registration {domain}")
            return {
                "success": False,
                "error": "API timeout",
                "domain": domain
            }
        except Exception as e:
            logger.error(f"Error registering domain {domain}: {e}")
            return {
                "success": False,
                "error": str(e),
                "domain": domain
            }
