# Exercise Analysis Lambda - Step 1

This is the Step 1 implementation of the exercise analysis system that processes workout videos uploaded to S3.

## Current Functionality (Step 1)

✅ **Complete Video Processing Pipeline:**
- Processes SQS messages from S3 video uploads
- Downloads MP4 files from S3 to Lambda `/tmp` directory
- Validates video format, size, and duration
- Extracts comprehensive video metadata
- Detailed logging throughout the process
- Proper error handling with DLQ support
- Automatic cleanup of downloaded files

## File Structure

```
exercise_analysis_lambda/
├── lambda_function.py      # Main Lambda handler
├── s3_client.py           # S3 download utility
├── video_processor.py     # Video validation & metadata extraction
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Configuration Constants

Located in `lambda_function.py`:
- `MAX_VIDEO_SIZE_MB = 500` - Maximum allowed video file size
- `MIN_DURATION_SECONDS = 10` - Minimum video duration
- `MAX_DURATION_SECONDS = 300` - Maximum video duration (5 minutes)

## Video Validation Rules

1. **File Format**: Must be `.mp4` extension
2. **File Size**: Must be ≤ 500MB
3. **Duration**: Must be between 10 seconds and 5 minutes
4. **Readability**: Must be able to read video frames without corruption

## Sample Output

When processing a valid video, the Lambda logs detailed metadata:

```json
{
  "duration_seconds": 45.67,
  "fps": 30.0,
  "frame_count": 1370,
  "width": 1920,
  "height": 1080,
  "resolution": "1920x1080",
  "file_size_bytes": 7816649,
  "file_size_mb": 7.45,
  "codec": "H264",
  "aspect_ratio": 1.78,
  "total_pixels": 2073600,
  "filename": "clip_20250716_160247.mp4",
  "is_valid_video": true
}
```

## Error Handling

The Lambda handles various error scenarios:
- **Invalid file format**: Logs error and sends to DLQ
- **File too large/small**: Logs error and sends to DLQ  
- **Duration out of range**: Logs error and sends to DLQ
- **Corrupted video**: Logs error and sends to DLQ
- **S3 access errors**: Logs error and sends to DLQ

All errors include correlation IDs for easy tracking in CloudWatch.

## Deployment Instructions

1. **Package the Lambda:**
   ```bash
   # Create deployment package
   zip -r exercise-analysis-lambda.zip .
   ```

2. **Update Lambda function:**
   - Upload the zip file to your existing Lambda function
   - Ensure the Lambda has proper IAM permissions for S3 access
   - Set memory to at least 1024MB (adjustable based on video sizes)
   - Set timeout to 15 minutes

3. **Required IAM Permissions:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:GetObject"
         ],
         "Resource": "arn:aws:s3:::exercise-tracker-fa20651d-064c-4a95-8540-edfe2af691cd/*"
       },
       {
         "Effect": "Allow",
         "Action": [
           "logs:CreateLogGroup",
           "logs:CreateLogStream",
           "logs:PutLogEvents"
         ],
         "Resource": "arn:aws:logs:us-west-2:*:*"
       }
     ]
   }
   ```

## Testing

1. **Upload a test video** (MP4, 10s-5min, <500MB) to your S3 bucket
2. **Check CloudWatch logs** for the Lambda function
3. **Verify SQS processing** - message should be consumed successfully
4. **Check for errors** - any validation failures will be logged

## Next Steps (Future Phases)

- **Phase 2**: Add MediaPipe pose estimation
- **Phase 3**: Implement exercise detection and rep counting  
- **Phase 4**: Add OpenAI coaching feedback
- **Phase 5**: PostgreSQL database integration

## Monitoring

Watch these CloudWatch metrics:
- Lambda invocations and errors
- SQS message processing
- Processing duration
- Memory usage

## Dependencies

- `boto3>=1.26.0` - AWS SDK
- `opencv-python>=4.8.0` - Video processing

---

**Status**: ✅ Step 1 Complete - Ready for deployment and testing 