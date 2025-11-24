"""Cloud storage client abstraction supporting S3, MinIO, and local storage."""
import os
import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO, Dict, Any
from pathlib import Path
import structlog

logger = structlog.get_logger()


class StorageClient:
    """Unified storage client for S3-compatible services."""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1", 
                 endpoint_url: Optional[str] = None, **kwargs):
        self.bucket_name = bucket_name
        self.region = region
        self.endpoint_url = endpoint_url
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            region_name=region,
            endpoint_url=endpoint_url,
            aws_access_key_id=kwargs.get('access_key'),
            aws_secret_access_key=kwargs.get('secret_key')
        )
        
        # Configure multipart upload for files > 5MB
        self.transfer_config = TransferConfig(
            multipart_threshold=1024 * 1024 * 5,  # 5MB
            max_concurrency=10,
            multipart_chunksize=1024 * 1024 * 5,
            use_threads=True
        )
        
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.info(f"Creating bucket {self.bucket_name}")
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                raise
    
    def upload_file(self, file_path: str, s3_key: str, 
                    metadata: Optional[Dict[str, str]] = None,
                    callback=None) -> bool:
        """Upload file to S3 with optional progress callback."""
        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args,
                Config=self.transfer_config,
                Callback=callback
            )
            
            logger.info(f"Uploaded {file_path} to s3://{self.bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Upload failed: {e}")
            return False
    
    def upload_fileobj(self, fileobj: BinaryIO, s3_key: str,
                       metadata: Optional[Dict[str, str]] = None) -> bool:
        """Upload file object to S3."""
        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.upload_fileobj(
                fileobj,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args,
                Config=self.transfer_config
            )
            
            logger.info(f"Uploaded fileobj to s3://{self.bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Upload failed: {e}")
            return False
    
    def list_objects(self, prefix: str = "") -> list:
        """List objects with given prefix."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            return response.get('Contents', [])
        except ClientError as e:
            logger.error(f"List failed: {e}")
            return []
    
    def get_object_metadata(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """Get object metadata."""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            logger.error(f"Get metadata failed: {e}")
            return None
    
    def delete_object(self, s3_key: str) -> bool:
        """Delete object from S3."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Deleted s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    def get_bucket_size(self) -> int:
        """Calculate total bucket size in bytes."""
        total_size = 0
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.bucket_name):
                for obj in page.get('Contents', []):
                    total_size += obj['Size']
        except ClientError as e:
            logger.error(f"Get bucket size failed: {e}")
        
        return total_size


class ProgressCallback:
    """Progress callback for uploads."""
    
    def __init__(self, filename: str, filesize: int):
        self.filename = filename
        self.filesize = filesize
        self.uploaded = 0
    
    def __call__(self, bytes_transferred: int):
        self.uploaded += bytes_transferred
        percentage = (self.uploaded / self.filesize) * 100
        logger.debug(f"{self.filename}: {percentage:.1f}% uploaded")
