"""
GitHub Service
Handles repository creation, commits, and branch management
"""
import httpx
import logging
import base64
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.services.config_service import ConfigService
from app.models.configuration import IntegrationType

logger = logging.getLogger(__name__)


class GitHubService:
    def __init__(self, db: Session):
        self.db = db
        self.config_service = ConfigService(db)
        self._api_token = None
        self._organization = None
        self._default_branch = None
        
    def _load_config(self):
        """Load GitHub configuration"""
        if self._api_token:
            return
            
        configs = self.config_service.get_all_by_type(IntegrationType.GITHUB)
        self._api_token = configs.get("api_token")
        self._organization = configs.get("organization")
        self._default_branch = configs.get("default_branch", "main")
        
        if not self._api_token:
            raise ValueError("GitHub API token not configured")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API headers"""
        return {
            "Authorization": f"token {self._api_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
    
    def _get_base_url(self) -> str:
        """Get base API URL (supports GitHub Enterprise)"""
        # For now, use standard GitHub API
        # Can be extended to support GitHub Enterprise
        return "https://api.github.com"
    
    async def create_repository(self, repo_name: str, private: bool = False, description: str = None) -> Dict[str, Any]:
        """
        Create a new GitHub repository
        
        Args:
            repo_name: Name of the repository
            private: Whether the repository should be private
            description: Repository description
            
        Returns:
            Dict with repository information
        """
        self._load_config()
        
        async with httpx.AsyncClient() as client:
            if self._organization:
                # Create in organization
                url = f"{self._get_base_url()}/orgs/{self._organization}/repos"
            else:
                # Create in user account
                url = f"{self._get_base_url()}/user/repos"
            
            payload = {
                "name": repo_name,
                "private": private,
                "auto_init": False,  # We'll push files manually
                "default_branch": self._default_branch
            }
            
            if description:
                payload["description"] = description
            
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 201:
                repo = response.json()
                logger.info(f"✅ Created GitHub repository: {repo_name}")
                return {
                    "success": True,
                    "repository": repo,
                    "clone_url": repo.get("clone_url"),
                    "ssh_url": repo.get("ssh_url"),
                    "html_url": repo.get("html_url")
                }
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("message", "Unknown error") if isinstance(error_data, dict) else str(error_data)
                logger.error(f"❌ Failed to create repository {repo_name}: {error_msg}")
                raise Exception(f"Failed to create GitHub repository: {error_msg}")
    
    async def get_repository(self, repo_name: str) -> Optional[Dict[str, Any]]:
        """Get repository information"""
        self._load_config()
        
        async with httpx.AsyncClient() as client:
            if self._organization:
                url = f"{self._get_base_url()}/repos/{self._organization}/{repo_name}"
            else:
                # Need to get username first
                user_response = await client.get(
                    f"{self._get_base_url()}/user",
                    headers=self._get_headers(),
                    timeout=10.0
                )
                if user_response.status_code != 200:
                    raise Exception("Failed to get GitHub user info")
                username = user_response.json().get("login")
                url = f"{self._get_base_url()}/repos/{username}/{repo_name}"
            
            response = await client.get(
                url,
                headers=self._get_headers(),
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("message", "Unknown error") if isinstance(error_data, dict) else str(error_data)
                raise Exception(f"Failed to get repository: {error_msg}")
    
    async def create_or_update_file(self, repo_name: str, file_path: str, content: bytes, message: str, branch: str = None) -> Dict[str, Any]:
        """
        Create or update a file in the repository
        
        Args:
            repo_name: Name of the repository
            file_path: Path to the file in the repository
            content: File content as bytes
            message: Commit message
            branch: Branch name (default: default_branch from config)
            
        Returns:
            Dict with commit information
        """
        self._load_config()
        
        if not branch:
            branch = self._default_branch
        
        # Encode content to base64
        content_b64 = base64.b64encode(content).decode('utf-8')
        
        async with httpx.AsyncClient() as client:
            # First, check if file exists
            if self._organization:
                repo_path = f"{self._organization}/{repo_name}"
            else:
                user_response = await client.get(
                    f"{self._get_base_url()}/user",
                    headers=self._get_headers(),
                    timeout=10.0
                )
                username = user_response.json().get("login")
                repo_path = f"{username}/{repo_name}"
            
            # Get file SHA if it exists
            file_url = f"{self._get_base_url()}/repos/{repo_path}/contents/{file_path}"
            file_response = await client.get(
                file_url,
                headers=self._get_headers(),
                params={"ref": branch},
                timeout=10.0
            )
            
            sha = None
            if file_response.status_code == 200:
                sha = file_response.json().get("sha")
            
            # Create or update file
            payload = {
                "message": message,
                "content": content_b64,
                "branch": branch
            }
            
            if sha:
                payload["sha"] = sha
            
            response = await client.put(
                file_url,
                headers=self._get_headers(),
                json=payload,
                timeout=30.0
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"✅ Created/updated file in {repo_name}: {file_path}")
                return {
                    "success": True,
                    "commit": result.get("commit"),
                    "content": result.get("content")
                }
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("message", "Unknown error") if isinstance(error_data, dict) else str(error_data)
                logger.error(f"❌ Failed to create/update file {file_path}: {error_msg}")
                raise Exception(f"Failed to create/update file: {error_msg}")
    
    async def commit_files(self, repo_name: str, files: Dict[str, bytes], message: str, branch: str = None) -> Dict[str, Any]:
        """
        Commit multiple files at once
        
        Args:
            repo_name: Name of the repository
            files: Dict mapping file paths to file contents (bytes)
            message: Commit message
            branch: Branch name (default: default_branch from config)
            
        Returns:
            Dict with commit information
        """
        self._load_config()
        
        if not branch:
            branch = self._default_branch
        
        results = []
        for file_path, content in files.items():
            try:
                result = await self.create_or_update_file(repo_name, file_path, content, message, branch)
                results.append({"file": file_path, "success": True, **result})
            except Exception as e:
                results.append({"file": file_path, "success": False, "error": str(e)})
        
        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"✅ Committed {success_count}/{len(files)} files to {repo_name}")
        
        return {
            "success": success_count == len(files),
            "files": results,
            "total": len(files),
            "succeeded": success_count
        }
    
    async def create_branch(self, repo_name: str, branch_name: str, from_branch: str = None) -> Dict[str, Any]:
        """Create a new branch"""
        self._load_config()
        
        if not from_branch:
            from_branch = self._default_branch
        
        async with httpx.AsyncClient() as client:
            if self._organization:
                repo_path = f"{self._organization}/{repo_name}"
            else:
                user_response = await client.get(
                    f"{self._get_base_url()}/user",
                    headers=self._get_headers(),
                    timeout=10.0
                )
                username = user_response.json().get("login")
                repo_path = f"{username}/{repo_name}"
            
            # Get SHA of the branch we're branching from
            ref_url = f"{self._get_base_url()}/repos/{repo_path}/git/ref/heads/{from_branch}"
            ref_response = await client.get(
                ref_url,
                headers=self._get_headers(),
                timeout=10.0
            )
            
            if ref_response.status_code != 200:
                raise Exception(f"Failed to get branch {from_branch}")
            
            sha = ref_response.json().get("object", {}).get("sha")
            
            # Create new branch
            new_ref_url = f"{self._get_base_url()}/repos/{repo_path}/git/refs"
            payload = {
                "ref": f"refs/heads/{branch_name}",
                "sha": sha
            }
            
            response = await client.post(
                new_ref_url,
                headers=self._get_headers(),
                json=payload,
                timeout=10.0
            )
            
            if response.status_code == 201:
                logger.info(f"✅ Created branch {branch_name} in {repo_name}")
                return {
                    "success": True,
                    "branch": response.json()
                }
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("message", "Unknown error") if isinstance(error_data, dict) else str(error_data)
                logger.error(f"❌ Failed to create branch {branch_name}: {error_msg}")
                raise Exception(f"Failed to create branch: {error_msg}")
