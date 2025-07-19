# Exercise Analysis System - Phase 1 Complete 🚀

This is a **Docker-based AWS Lambda system** for analyzing exercise videos with comprehensive local development support.

## ✅ Phase 1 - Container & Local Development (COMPLETE)

### **Dual Execution Support:**
- **🐳 Docker Container**: Deployable to AWS Lambda as container image
- **💻 Local Development**: Run directly on your machine for debugging
- **🔧 Interactive Testing**: Development server with command-line interface
- **📊 Performance Profiling**: Built-in timing and optimization tools

### **Complete Video Processing Pipeline:**
- Processes SQS messages from S3 video uploads
- Downloads MP4 files from S3 or processes local files
- Validates video format, size, and duration (10s-5min, <500MB)
- Extracts comprehensive video metadata (resolution, fps, codec, etc.)
- Environment-aware configuration system
- Detailed logging with correlation IDs
- Proper error handling with DLQ support
- Automatic cleanup of downloaded files

## 🗂️ Project Structure

```
exercise_analysis_lambda/
├── 🐳 Container & Deployment
│   ├── Dockerfile                  # Lambda container configuration
│   ├── requirements.txt           # Python dependencies
│   └── README.md                 # This documentation
├── 🧠 Core Application
│   ├── lambda_function.py         # Main handler (dual execution)
│   ├── s3_client.py              # S3 download utility
│   ├── video_processor.py        # Video validation & metadata
│   └── config.py                 # Centralized configuration
├── 🔧 Development Tools
│   ├── local_runner.py           # Advanced local development server
│   └── mock_events/              # Sample SQS events for testing
│       ├── sample_pushup_video.json
│       ├── sample_rowing_video.json
│       ├── sample_dumbbell_video.json
│       └── README.md
└── 📁 Local Directories (auto-created)
    ├── temp/                     # Temporary processing files
    ├── test_videos/             # Local test video files
    ├── output/                  # Processing results
    ├── debug_output/            # Debug frames and analysis
    └── logs/                    # Local log files
```

## ⚙️ Configuration System

**Environment-Aware Configuration** in `config.py`:
- **Lambda**: Optimized for production (less logging, cleanup enabled)
- **Container**: Balanced settings for containerized deployment
- **Local**: Developer-friendly (debug logging, frame saving, profiling)

### Key Configuration Categories:
- **Video Processing**: Size limits, duration, supported formats
- **AWS Settings**: Region, S3 bucket, SNS/SQS configuration
- **Exercise Analysis**: Supported exercises, confidence thresholds
- **User Profile**: Weight, height, age for calorie calculations
- **Development**: Logging, debugging, profiling options

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

## 🚀 Local Development Usage

### **1. Quick Start - Process Local Video**
```bash
# Process a local video file directly
python lambda_function.py --video /path/to/your/video.mp4

# With debug logging for detailed information  
python lambda_function.py --video workout.mp4 --debug
```

### **2. Interactive Development Server**
```bash
# Start interactive server for experimentation
python local_runner.py server

# In the server prompt:
exercise-analysis> process-local test_videos/pushups.mp4
exercise-analysis> process-s3 your-bucket video.mp4
exercise-analysis> generate-mock
exercise-analysis> help
```

### **3. Advanced Development Tools**
```bash
# Batch process multiple videos
python local_runner.py batch --directory ./test_videos --output results.json

# Profile performance for optimization
python local_runner.py profile --video test.mp4 --iterations 5

# Generate test data and mock events
python local_runner.py generate-test-data

# View current configuration
python config.py
```

### **4. Test with Mock SQS Events**
```bash
# Process mock S3 events (no actual AWS calls)
python lambda_function.py --mock-event mock_events/sample_pushup_video.json

# Test different exercise types
python lambda_function.py --mock-event mock_events/sample_rowing_video.json --debug
```

### **5. Environment Variables Override**
```bash
# Override configuration at runtime
export EXERCISE_ANALYSIS_MAX_VIDEO_SIZE_MB=1000
export EXERCISE_ANALYSIS_LOG_LEVEL=DEBUG
export EXERCISE_ANALYSIS_USER_WEIGHT_KG=70

python lambda_function.py --video test.mp4
```

## 🐳 Container Deployment

### **1. Build Docker Image**
```bash
# Build the container image
docker build -t exercise-analysis .

# Test locally first
docker run --rm -v $(pwd)/test_videos:/videos exercise-analysis python lambda_function.py --video /videos/test.mp4
```

### **2. Deploy to AWS Lambda**
```bash
# Tag for your ECR repository
docker tag exercise-analysis:latest YOUR_ECR_URI:latest

# Push to ECR
docker push YOUR_ECR_URI:latest

# Update Lambda function to use container image
aws lambda update-function-code \
  --function-name exercise-tracker-dev-pose-analysis \
  --image-uri YOUR_ECR_URI:latest
```

### **3. Required IAM Permissions**
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

## 🎯 Next Steps - Phase 2: Exercise Detection & Pose Analysis

With Phase 1 complete, the foundation is solid for adding ML-powered exercise analysis:

### **Phase 2 Goals:**
- **🤖 MediaPipe Integration**: Human pose estimation from video frames
- **🏋️ Exercise Detection**: Auto-identify push-ups, rowing, dumbbell exercises
- **📊 Rep Counting**: Accurate repetition counting with form analysis
- **📐 Form Analysis**: Joint angle measurements and movement quality scoring

### **Phase 3 Goals:**
- **🧠 AI Coaching**: OpenAI-powered personalized feedback and tips
- **🔥 Calorie Calculation**: Accurate calorie burn estimation using MET values
- **📈 Performance Metrics**: Detailed form scoring and improvement suggestions

### **Phase 4 Goals:**
- **🗄️ Database Integration**: PostgreSQL storage for exercise history
- **📊 Progress Tracking**: Long-term trends and performance analytics
- **🎯 Goal Setting**: Personal targets and achievement tracking

### **Phase 5 Goals:**
- **📱 API Development**: REST API for external integrations
- **🔔 Notifications**: Real-time alerts and progress updates
- **🌐 Web Dashboard**: Interactive UI for viewing analysis results

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

## 📊 Development Status

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1** | ✅ **COMPLETE** | Container deployment, local development, video processing |
| **Phase 2** | 🔄 **NEXT** | MediaPipe pose estimation, exercise detection, rep counting |
| **Phase 3** | ⏳ **PLANNED** | AI coaching feedback, calorie calculation, performance metrics |
| **Phase 4** | ⏳ **PLANNED** | Database integration, progress tracking, goal setting |
| **Phase 5** | ⏳ **PLANNED** | API development, notifications, web dashboard |

---

**Current Status**: ✅ **Phase 1 Complete** - Production-ready container with comprehensive local development tools

**Ready for**: Docker deployment to AWS Lambda, local development and testing, mock event processing 