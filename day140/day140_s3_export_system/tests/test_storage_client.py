"""Tests for storage client."""
import pytest
from moto import mock_aws
import boto3
from src.storage.client import StorageClient

@mock_aws
def test_storage_client_initialization():
    """Test storage client initialization."""
    client = StorageClient(
        bucket_name='test-bucket',
        region='us-east-1'
    )
    assert client.bucket_name == 'test-bucket'

@mock_aws
def test_bucket_creation():
    """Test bucket creation."""
    s3 = boto3.client('s3', region_name='us-east-1')
    
    client = StorageClient(
        bucket_name='test-bucket',
        region='us-east-1'
    )
    
    buckets = s3.list_buckets()
    bucket_names = [b['Name'] for b in buckets['Buckets']]
    assert 'test-bucket' in bucket_names

@mock_aws
def test_file_upload():
    """Test file upload to S3."""
    import tempfile
    
    client = StorageClient(
        bucket_name='test-bucket',
        region='us-east-1'
    )
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write('test content')
        temp_file = f.name
    
    # Upload file
    success = client.upload_file(temp_file, 'test.txt')
    assert success == True
    
    # Verify upload
    objects = client.list_objects()
    assert len(objects) > 0
