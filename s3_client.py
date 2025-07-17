"""
S3 Client utility for downloading exercise videos
"""

import logging
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from typing import Optional

logger = logging.getLogger(__name__)

class S3Client:
    """
    S3 client wrapper for downloading video files
    """
    
    def __init__(self, region_name: str = 'us-west-2'):
        """
        Initialize S3 client
        
        Args:
            region_name: AWS region (default: us-west-2)
        """
        try:
            self.s3_client = boto3.client('s3', region_name=region_name)
            logger.info(f"Initialized S3 client for region: {region_name}")
        except (NoCredentialsError, Exception) as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise e
    
    def download_file(self, bucket_name: str, object_key: str, local_file_path: str) -> None:
        """
        Download a file from S3 to local filesystem
        
        Args:
            bucket_name: S3 bucket name
            object_key: S3 object key (file path)
            local_file_path: Local path where file should be saved
            
        Raises:
            Exception: If download fails
        """
        try:
            logger.info(f"Downloading s3://{bucket_name}/{object_key} to {local_file_path}")
            
            # Download file from S3
            self.s3_client.download_file(bucket_name, object_key, local_file_path)
            
            logger.info(f"Successfully downloaded file from S3")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            
            if error_code == 'NoSuchKey':
                raise FileNotFoundError(f"File not found in S3: s3://{bucket_name}/{object_key}")
            elif error_code == 'NoSuchBucket':
                raise FileNotFoundError(f"Bucket not found: {bucket_name}")
            elif error_code == 'AccessDenied':
                raise PermissionError(f"Access denied to S3 resource: s3://{bucket_name}/{object_key}")
            else:
                raise Exception(f"S3 download failed ({error_code}): {error_msg}")
                
        except Exception as e:
            logger.error(f"Unexpected error downloading from S3: {str(e)}")
            raise e
    
    def get_object_metadata(self, bucket_name: str, object_key: str) -> dict:
        """
        Get metadata for an S3 object without downloading it
        
        Args:
            bucket_name: S3 bucket name
            object_key: S3 object key
            
        Returns:
            dict: Object metadata
        """
        try:
            logger.info(f"Getting metadata for s3://{bucket_name}/{object_key}")
            
            response = self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
            
            metadata = {
                'size': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'content_type': response.get('ContentType'),
                'etag': response.get('ETag', '').strip('"'),
                'metadata': response.get('Metadata', {})
            }
            
            logger.info(f"Retrieved metadata for S3 object: size={metadata['size']} bytes")
            return metadata
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'NoSuchKey':
                raise FileNotFoundError(f"File not found in S3: s3://{bucket_name}/{object_key}")
            elif error_code == 'NoSuchBucket':
                raise FileNotFoundError(f"Bucket not found: {bucket_name}")
            else:
                raise Exception(f"Failed to get S3 object metadata: {str(e)}")
                
        except Exception as e:
            logger.error(f"Unexpected error getting S3 metadata: {str(e)}")
            raise e 