from minio import Minio
from minio.error import S3Error
from app.config import settings
import logging
from io import BytesIO
from typing import BinaryIO

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket already exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error checking/creating bucket: {e}")
            raise
    
    def upload_file(
        self,
        file_data: bytes,
        object_name: str,
        content_type: str,
        metadata: dict = None
    ) -> str:
        """
        Upload a file to MinIO.
        
        Args:
            file_data: File content as bytes
            object_name: Name/path of the object in MinIO
            content_type: MIME type of the file
            metadata: Optional metadata dict
            
        Returns:
            str: Object name/path in MinIO
        """
        try:
            file_stream = BytesIO(file_data)
            file_size = len(file_data)
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_stream,
                length=file_size,
                content_type=content_type,
                metadata=metadata or {}
            )
            
            logger.info(f"Uploaded file: {object_name} ({file_size} bytes)")
            return object_name
            
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    def download_file(self, object_name: str) -> bytes:
        """
        Download a file from MinIO.
        
        Args:
            object_name: Name/path of the object in MinIO
            
        Returns:
            bytes: File content
        """
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"Downloaded file: {object_name}")
            return data
            
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    def delete_file(self, object_name: str) -> bool:
        """
        Delete a file from MinIO.
        
        Args:
            object_name: Name/path of the object in MinIO
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            logger.info(f"Deleted file: {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            raise
    
    def file_exists(self, object_name: str) -> bool:
        """Check if a file exists in MinIO."""
        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            return True
        except S3Error:
            return False
    
    def get_file_url(self, object_name: str, expires: int = 3600) -> str:
        """
        Get a presigned URL for a file (valid for limited time).
        
        Args:
            object_name: Name/path of the object in MinIO
            expires: URL expiration time in seconds (default 1 hour)
            
        Returns:
            str: Presigned URL
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise


# Singleton instance
storage_service = StorageService()