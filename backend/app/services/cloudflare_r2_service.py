"""
Cloudflare R2 Service
Handles file upload/download to Cloudflare R2 storage
"""
import boto3
import logging
from typing import Optional, Dict, Any, BinaryIO
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session
from app.services.config_service import ConfigService
from app.models.configuration import IntegrationType

logger = logging.getLogger(__name__)


class CloudflareR2Service:
    def __init__(self, db: Session):
        self.db = db
        self.config_service = ConfigService(db)
        self._s3_client = None
        self._bucket_name = None
        self._endpoint_url = None
        
    def _load_config(self):
        """Load R2 configuration and initialize S3 client"""
        if self._s3_client:
            return
            
        configs = self.config_service.get_all_by_type(IntegrationType.CLOUDFLARE_R2)
        
        self._bucket_name = configs.get("bucket_name")
        self._endpoint_url = configs.get("endpoint_url")
        access_key_id = configs.get("access_key_id")
        secret_access_key = configs.get("secret_access_key")
        region = configs.get("region", "auto")
        
        if not self._bucket_name or not access_key_id or not secret_access_key:
            raise ValueError("R2 configuration incomplete. Missing bucket_name, access_key_id, or secret_access_key")
        
        # Build endpoint URL if not provided
        if not self._endpoint_url:
            # Extract account ID from access key or use default format
            # R2 endpoint format: https://{account_id}.r2.cloudflarestorage.com
            # For now, we'll try to construct it or use a default
            self._endpoint_url = f"https://{access_key_id[:8]}.r2.cloudflarestorage.com"
        
        self._s3_client = boto3.client(
            's3',
            endpoint_url=self._endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region
        )
    
    def upload_file(self, key: str, file_content: bytes, content_type: str = None) -> Dict[str, Any]:
        """
        Upload a file to R2
        
        Args:
            key: Object key (path) in the bucket
            file_content: File content as bytes
            content_type: MIME type (optional)
            
        Returns:
            Dict with upload information
        """
        self._load_config()
        
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self._s3_client.put_object(
                Bucket=self._bucket_name,
                Key=key,
                Body=file_content,
                **extra_args
            )
            
            # Generate public URL (if bucket is public) or presigned URL
            url = f"{self._endpoint_url}/{self._bucket_name}/{key}"
            
            logger.info(f"✅ Uploaded file to R2: {key}")
            return {
                "success": True,
                "key": key,
                "url": url,
                "bucket": self._bucket_name
            }
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"❌ Failed to upload file {key}: {error_code} - {e}")
            raise Exception(f"Failed to upload file: {error_code} - {str(e)}")
    
    def upload_file_from_path(self, key: str, file_path: str, content_type: str = None) -> Dict[str, Any]:
        """
        Upload a file from local path to R2
        
        Args:
            key: Object key (path) in the bucket
            file_path: Local file path
            content_type: MIME type (optional)
            
        Returns:
            Dict with upload information
        """
        with open(file_path, 'rb') as f:
            return self.upload_file(key, f.read(), content_type)
    
    def download_file(self, key: str) -> bytes:
        """
        Download a file from R2
        
        Args:
            key: Object key (path) in the bucket
            
        Returns:
            File content as bytes
        """
        self._load_config()
        
        try:
            response = self._s3_client.get_object(
                Bucket=self._bucket_name,
                Key=key
            )
            return response['Body'].read()
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'NoSuchKey':
                raise FileNotFoundError(f"File not found: {key}")
            logger.error(f"❌ Failed to download file {key}: {error_code} - {e}")
            raise Exception(f"Failed to download file: {error_code} - {str(e)}")
    
    def delete_file(self, key: str) -> bool:
        """
        Delete a file from R2
        
        Args:
            key: Object key (path) in the bucket
            
        Returns:
            True if successful
        """
        self._load_config()
        
        try:
            self._s3_client.delete_object(
                Bucket=self._bucket_name,
                Key=key
            )
            logger.info(f"✅ Deleted file from R2: {key}")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"❌ Failed to delete file {key}: {error_code} - {e}")
            raise Exception(f"Failed to delete file: {error_code} - {str(e)}")
    
    def list_files(self, prefix: str = "") -> list:
        """
        List files in R2 bucket
        
        Args:
            prefix: Prefix to filter files (optional)
            
        Returns:
            List of file keys
        """
        self._load_config()
        
        try:
            response = self._s3_client.list_objects_v2(
                Bucket=self._bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        "key": obj['Key'],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat()
                    })
            
            return files
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"❌ Failed to list files: {error_code} - {e}")
            raise Exception(f"Failed to list files: {error_code} - {str(e)}")
    
    def get_public_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for temporary access
        
        Args:
            key: Object key (path) in the bucket
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL
        """
        self._load_config()
        
        try:
            url = self._s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self._bucket_name, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"❌ Failed to generate presigned URL for {key}: {error_code} - {e}")
            raise Exception(f"Failed to generate presigned URL: {error_code} - {str(e)}")
