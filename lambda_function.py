"""
Exercise Analysis Function - Dual Execution Support
==================================================
This module supports both AWS Lambda and local execution:

1. LAMBDA MODE: Processes SQS messages from AWS Lambda runtime
2. LOCAL MODE: Can be run directly for development/testing

Environment Detection:
- Lambda: Detected via AWS_LAMBDA_FUNCTION_NAME environment variable
- Local: Detected via absence of Lambda env vars or --local flag

Usage Examples:
- Lambda: Automatically triggered by SQS messages
- Local: python lambda_function.py --local --video test.mp4
- Local: python lambda_function.py --mock-sqs-event mock_events/sample.json
"""

import json
import logging
import os
import sys
import argparse
import tempfile
from typing import Dict, Any, Optional, Union
from pathlib import Path

from s3_client import S3Client
from video_processor import VideoProcessor

# ============================================================================
# CONFIGURATION AND ENVIRONMENT DETECTION
# ============================================================================

# Import configuration system
from config import get_config, is_development_mode

# Get application configuration
config = get_config()

# Environment Detection
def is_lambda_environment() -> bool:
    """
    Detect if we're running in AWS Lambda environment
    
    Detection Methods:
    1. AWS_LAMBDA_FUNCTION_NAME environment variable (primary)
    2. AWS_EXECUTION_ENV environment variable (secondary)
    3. LAMBDA_TASK_ROOT environment variable (tertiary)
    
    Returns:
        bool: True if running in Lambda, False if local
    """
    lambda_indicators = [
        'AWS_LAMBDA_FUNCTION_NAME',
        'AWS_EXECUTION_ENV', 
        'LAMBDA_TASK_ROOT'
    ]
    
    return any(os.getenv(indicator) for indicator in lambda_indicators)

def is_container_environment() -> bool:
    """
    Detect if we're running in a Docker container
    
    Returns:
        bool: True if running in container, False otherwise
    """
    return os.getenv('RUNNING_IN_CONTAINER', 'false').lower() == 'true'

# Configure logging based on environment
def setup_logging() -> logging.Logger:
    """
    Configure logging based on execution environment
    
    Lambda: Uses AWS's default CloudWatch integration (minimal configuration)
    Local: Human-readable format for development
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Get logger for this module
    logger = logging.getLogger(__name__)
    
    if is_lambda_environment():
        # Lambda environment - use AWS's default CloudWatch setup
        # AWS Lambda automatically configures logging for CloudWatch
        # Just set the level, don't call basicConfig or add handlers
        logger.setLevel(logging.INFO)
        logging.getLogger().setLevel(logging.INFO)  # Set root logger level
        
    else:
        # Local environment - developer-friendly logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        logger.setLevel(logging.DEBUG)
    
    # Log environment detection
    env_type = "Lambda" if is_lambda_environment() else "Local"
    container = "Container" if is_container_environment() else "Native"
    logger.info(f"Exercise Analysis starting in {env_type} environment ({container})")
    
    return logger

# Initialize logger
logger = setup_logging()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for exercise video analysis - Step 1
    Processes SQS messages containing S3 video upload notifications
    """
    correlation_id = context.aws_request_id
    
    # Test logging to ensure CloudWatch integration is working
    print(f"[{correlation_id}] Lambda handler started - print statement test")
    logger.info(f"[{correlation_id}] Lambda handler started - logger test")
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
    
    if size_mb > config.MAX_VIDEO_SIZE_MB:
        error_msg = f"Video file too large: {size_mb:.2f}MB > {config.MAX_VIDEO_SIZE_MB}MB limit"
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
    if duration_seconds < config.MIN_DURATION_SECONDS:
        error_msg = f"Video too short: {duration_seconds}s < {config.MIN_DURATION_SECONDS}s minimum"
        logger.error(f"[{correlation_id}] {error_msg}")
        raise ValueError(error_msg)
    
    if duration_seconds > config.MAX_DURATION_SECONDS:
        error_msg = f"Video too long: {duration_seconds}s > {config.MAX_DURATION_SECONDS}s maximum"
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

# ============================================================================
# LOCAL EXECUTION SUPPORT
# ============================================================================

def generate_correlation_id() -> str:
    """
    Generate a correlation ID for local execution (mimics Lambda's request ID)
    
    Returns:
        str: Unique correlation ID
    """
    import uuid
    return str(uuid.uuid4())

def create_mock_context(correlation_id: Optional[str] = None):
    """
    Create a mock Lambda context for local execution
    
    Args:
        correlation_id: Optional correlation ID, generates one if not provided
        
    Returns:
        Mock context object with aws_request_id attribute
    """
    class MockLambdaContext:
        def __init__(self, request_id: str):
            self.aws_request_id = request_id
            self.function_name = "exercise-tracker-dev-pose-analysis-local"
            self.function_version = "local"
            self.memory_limit_in_mb = 1024
            
    return MockLambdaContext(correlation_id or generate_correlation_id())

def process_local_video_file(video_path: str) -> Dict[str, Any]:
    """
    Process a local video file (for development/testing)
    
    Args:
        video_path: Path to local video file
        
    Returns:
        dict: Processing results
    """
    correlation_id = generate_correlation_id()
    logger.info(f"[{correlation_id}] Processing local video file: {video_path}")
    
    try:
        # Validate file exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Get file info
        file_size = os.path.getsize(video_path)
        logger.info(f"[{correlation_id}] Local file size: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
        
        # Validate file size and extension
        validate_file_size(file_size, correlation_id)
        validate_file_extension(video_path, correlation_id)
        
        # Process video metadata
        video_metadata = validate_and_extract_metadata(video_path, correlation_id)
        
        logger.info(f"[{correlation_id}] Local video processing successful")
        logger.info(f"[{correlation_id}] Video metadata: {json.dumps(video_metadata, indent=2)}")
        
        return {
            'statusCode': 200,
            'correlation_id': correlation_id,
            'video_metadata': video_metadata,
            'message': 'Local video processing completed successfully'
        }
        
    except Exception as e:
        logger.error(f"[{correlation_id}] Error processing local video: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'correlation_id': correlation_id,
            'error': str(e),
            'message': 'Local video processing failed'
        }

def create_mock_sqs_event(s3_bucket: str, s3_key: str) -> Dict[str, Any]:
    """
    Create a mock SQS event for local testing
    
    Args:
        s3_bucket: S3 bucket name
        s3_key: S3 object key
        
    Returns:
        dict: Mock SQS event structure
    """
    return {
        "Records": [
            {
                "body": json.dumps({
                    "Type": "Notification",
                    "MessageId": f"local-test-{generate_correlation_id()}",
                    "TopicArn": "arn:aws:sns:us-west-2:123456789012:exercise-tracker-dev-video-upload-notifications",
                    "Subject": "Amazon S3 Notification",
                    "Message": json.dumps({
                        "Records": [
                            {
                                "eventVersion": "2.1",
                                "eventSource": "aws:s3",
                                "awsRegion": "us-west-2",
                                "eventTime": "2025-01-01T12:00:00.000Z",
                                "eventName": "ObjectCreated:Put",
                                "s3": {
                                    "bucket": {"name": s3_bucket},
                                    "object": {
                                        "key": s3_key,
                                        "size": 1000000  # Mock size
                                    }
                                }
                            }
                        ]
                    })
                })
            }
        ]
    }

def parse_local_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for local execution
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Exercise Analysis - Local Development Mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process local video file
  python lambda_function.py --local --video /path/to/video.mp4
  
  # Process S3 file locally
  python lambda_function.py --s3-bucket my-bucket --s3-key video.mp4
  
  # Process mock SQS event from file
  python lambda_function.py --mock-event mock_events/sample.json
        """
    )
    
    # Execution mode
    parser.add_argument('--local', action='store_true', 
                       help='Force local execution mode')
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    
    input_group.add_argument('--video', type=str,
                           help='Path to local video file for processing')
    
    input_group.add_argument('--s3-bucket', type=str,
                           help='S3 bucket name (use with --s3-key)')
    
    input_group.add_argument('--mock-event', type=str,
                           help='Path to JSON file containing mock SQS event')
    
    # S3 key (required if s3-bucket is specified)
    parser.add_argument('--s3-key', type=str,
                       help='S3 object key (required with --s3-bucket)')
    
    # Optional arguments
    parser.add_argument('--correlation-id', type=str,
                       help='Custom correlation ID for tracking')
    
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    return parser.parse_args()

def main():
    """
    Main entry point for local execution
    """
    # Parse command line arguments
    args = parse_local_arguments()
    
    # Adjust logging level if debug requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Validate argument combinations
    if args.s3_bucket and not args.s3_key:
        logger.error("--s3-key is required when using --s3-bucket")
        sys.exit(1)
    
    try:
        if args.video:
            # Process local video file
            result = process_local_video_file(args.video)
            
        elif args.s3_bucket and args.s3_key:
            # Process S3 file using mock SQS event
            mock_event = create_mock_sqs_event(args.s3_bucket, args.s3_key)
            mock_context = create_mock_context(args.correlation_id)
            result = lambda_handler(mock_event, mock_context)
            
        elif args.mock_event:
            # Process mock event from file
            with open(args.mock_event, 'r') as f:
                mock_event = json.load(f)
            mock_context = create_mock_context(args.correlation_id)
            result = lambda_handler(mock_event, mock_context)
            
        else:
            logger.error("No valid input option provided")
            sys.exit(1)
        
        # Print results
        logger.info("Processing completed successfully")
        print(json.dumps(result, indent=2))
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}", exc_info=True)
        sys.exit(1)

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # When run directly (not imported), start local execution
    main() 