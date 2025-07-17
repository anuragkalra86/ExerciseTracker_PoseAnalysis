"""
AWS Lambda Function: Exercise Analysis - Step 1
Processes SQS messages, downloads videos from S3, validates format and extracts metadata
"""

import json
import logging
import os
import tempfile
from typing import Dict, Any

from s3_client import S3Client
from video_processor import VideoProcessor

# TODO: Move these constants to a config file in future
MAX_VIDEO_SIZE_MB = 500
MIN_DURATION_SECONDS = 10
MAX_DURATION_SECONDS = 300  # 5 minutes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for exercise video analysis - Step 1
    Processes SQS messages containing S3 video upload notifications
    """
    correlation_id = context.aws_request_id
    logger.info(f"[{correlation_id}] Starting exercise analysis Lambda - Step 1")
    
    try:
        # Process each SQS record (should be only one based on our configuration)
        for record in event.get('Records', []):
            process_sqs_record(record, correlation_id)
            
        logger.info(f"[{correlation_id}] Successfully completed processing")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed video(s)',
                'correlation_id': correlation_id
            })
        }
        
    except Exception as e:
        logger.error(f"[{correlation_id}] Fatal error in lambda_handler: {str(e)}", exc_info=True)
        # Re-raise to send message to DLQ
        raise e

def process_sqs_record(record: Dict[str, Any], correlation_id: str) -> None:
    """
    Process a single SQS record containing SNS notification with S3 event
    """
    logger.info(f"[{correlation_id}] Processing SQS record")
    
    try:
        # Parse SNS message from SQS record
        sns_message = parse_sns_message(record)
        
        # Extract S3 event information
        s3_events = parse_s3_events(sns_message)
        
        # Process each S3 event (typically one per message)
        for s3_event in s3_events:
            process_s3_event(s3_event, correlation_id)
            
    except Exception as e:
        logger.error(f"[{correlation_id}] Error processing SQS record: {str(e)}", exc_info=True)
        raise e

def parse_sns_message(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and parse SNS message from SQS record
    """
    try:
        # The record body contains the SNS message
        sns_message = json.loads(record['body'])
        logger.info(f"Parsed SNS message with MessageId: {sns_message.get('MessageId')}")
        return sns_message
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Failed to parse SNS message from SQS record: {str(e)}")

def parse_s3_events(sns_message: Dict[str, Any]) -> list:
    """
    Extract S3 events from SNS message
    """
    try:
        # The SNS Message field contains JSON string with S3 events
        s3_message_str = sns_message['Message']
        s3_message = json.loads(s3_message_str)
        s3_events = s3_message.get('Records', [])
        
        logger.info(f"Found {len(s3_events)} S3 event(s) in SNS message")
        return s3_events
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Failed to parse S3 events from SNS message: {str(e)}")

def process_s3_event(s3_event: Dict[str, Any], correlation_id: str) -> None:
    """
    Process a single S3 event - download and validate video
    """
    try:
        # Extract S3 information
        bucket_name = s3_event['s3']['bucket']['name']
        object_key = s3_event['s3']['object']['key']
        object_size = s3_event['s3']['object']['size']
        event_name = s3_event.get('eventName', 'Unknown')
        
        logger.info(f"[{correlation_id}] Processing S3 event: {event_name}")
        logger.info(f"[{correlation_id}] Bucket: {bucket_name}")
        logger.info(f"[{correlation_id}] Object: {object_key}")
        logger.info(f"[{correlation_id}] Size: {object_size} bytes ({object_size / 1024 / 1024:.2f} MB)")
        
        # Validate file size before download
        validate_file_size(object_size, correlation_id)
        
        # Validate file extension
        validate_file_extension(object_key, correlation_id)
        
        # Download video file
        local_file_path = download_video_file(bucket_name, object_key, correlation_id)
        
        try:
            # Validate and extract video metadata
            video_metadata = validate_and_extract_metadata(local_file_path, correlation_id)
            
            logger.info(f"[{correlation_id}] Video validation successful")
            logger.info(f"[{correlation_id}] Video metadata: {json.dumps(video_metadata, indent=2)}")
            
            # TODO: In future phases, this is where we'll:
            # - Save to database with status 'processing'
            # - Trigger pose analysis
            # - Calculate calories and get coaching feedback
            
        finally:
            # Always clean up the downloaded file
            cleanup_file(local_file_path, correlation_id)
            
    except Exception as e:
        logger.error(f"[{correlation_id}] Error processing S3 event: {str(e)}", exc_info=True)
        raise e

def validate_file_size(size_bytes: int, correlation_id: str) -> None:
    """
    Validate video file size is within acceptable limits
    """
    size_mb = size_bytes / 1024 / 1024
    
    if size_mb > MAX_VIDEO_SIZE_MB:
        error_msg = f"Video file too large: {size_mb:.2f}MB > {MAX_VIDEO_SIZE_MB}MB limit"
        logger.error(f"[{correlation_id}] {error_msg}")
        raise ValueError(error_msg)
    
    logger.info(f"[{correlation_id}] File size validation passed: {size_mb:.2f}MB")

def validate_file_extension(object_key: str, correlation_id: str) -> None:
    """
    Validate file has MP4 extension
    """
    if not object_key.lower().endswith('.mp4'):
        error_msg = f"Invalid file format: {object_key}. Only MP4 files are supported."
        logger.error(f"[{correlation_id}] {error_msg}")
        raise ValueError(error_msg)
    
    logger.info(f"[{correlation_id}] File extension validation passed: MP4")

def download_video_file(bucket_name: str, object_key: str, correlation_id: str) -> str:
    """
    Download video file from S3 to Lambda /tmp directory
    """
    logger.info(f"[{correlation_id}] Starting video download from S3")
    
    s3_client = S3Client()
    
    # Create temporary file in /tmp directory
    temp_dir = "/tmp"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Use original filename for easier debugging
    filename = os.path.basename(object_key)
    local_file_path = os.path.join(temp_dir, f"{correlation_id}_{filename}")
    
    try:
        s3_client.download_file(bucket_name, object_key, local_file_path)
        
        # Verify download
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"Downloaded file not found: {local_file_path}")
        
        file_size = os.path.getsize(local_file_path)
        logger.info(f"[{correlation_id}] Successfully downloaded video: {file_size} bytes")
        
        return local_file_path
        
    except Exception as e:
        # Clean up partial download if it exists
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
        raise e

def validate_and_extract_metadata(file_path: str, correlation_id: str) -> Dict[str, Any]:
    """
    Validate video format and extract metadata
    """
    logger.info(f"[{correlation_id}] Starting video validation and metadata extraction")
    
    video_processor = VideoProcessor()
    
    # Extract metadata and validate
    metadata = video_processor.extract_metadata(file_path)
    
    # Validate duration
    duration_seconds = metadata.get('duration_seconds', 0)
    if duration_seconds < MIN_DURATION_SECONDS:
        error_msg = f"Video too short: {duration_seconds}s < {MIN_DURATION_SECONDS}s minimum"
        logger.error(f"[{correlation_id}] {error_msg}")
        raise ValueError(error_msg)
    
    if duration_seconds > MAX_DURATION_SECONDS:
        error_msg = f"Video too long: {duration_seconds}s > {MAX_DURATION_SECONDS}s maximum"
        logger.error(f"[{correlation_id}] {error_msg}")
        raise ValueError(error_msg)
    
    logger.info(f"[{correlation_id}] Video duration validation passed: {duration_seconds}s")
    
    # Validate that it's a proper video file
    if not metadata.get('is_valid_video', False):
        error_msg = "Invalid or corrupted video file"
        logger.error(f"[{correlation_id}] {error_msg}")
        raise ValueError(error_msg)
    
    logger.info(f"[{correlation_id}] Video format validation passed")
    
    return metadata

def cleanup_file(file_path: str, correlation_id: str) -> None:
    """
    Clean up downloaded file from /tmp directory
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"[{correlation_id}] Successfully cleaned up file: {file_path}")
        else:
            logger.warning(f"[{correlation_id}] File not found for cleanup: {file_path}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Error cleaning up file {file_path}: {str(e)}")
        # Don't raise exception for cleanup errors 