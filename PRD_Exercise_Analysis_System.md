# Product Requirements Document: Exercise Analysis System

## 1. Overview

### Project Vision
Build an automated exercise analysis system that processes home gym workout videos to provide insights on form, performance, and improvement recommendations.

### Key Objectives
- Analyze exercise form and technique
- Calculate calories burned
- Provide coaching feedback and improvement suggestions
- Track exercise performance over time
- Maintain detailed exercise history

## 2. System Architecture

### High-Level Flow
```
MP4 Upload → S3 → SNS → SQS → Lambda → Video Analysis → PostgreSQL → Results
```

### Components
1. **AWS Lambda**: `exercise-tracker-dev-pose-analysis`
   - Runtime: Python 3.13
   - Memory: 1024MB+ (configurable)
   - Timeout: 15 minutes
   - Region: us-west-2

2. **S3 Bucket**: `exercise-tracker-fa20651d-064c-4a95-8540-edfe2af691cd`
   - Stores MP4 video files
   - Triggers SNS on upload

3. **PostgreSQL Database**: Amazon Aurora
   - User profiles
   - Exercise sessions
   - Analysis results (JSONB)

4. **External APIs**:
   - MediaPipe (Google) for pose estimation
   - OpenAI API for coaching feedback

## 3. Supported Exercises (MVP)

### Included Exercises
- **Push-ups**: Full body pose detection, rep counting, form analysis
- **Rowing**: Full body motion tracking, stroke analysis
- **Dumbbell Side Lateral Raises**: Arm/shoulder movement analysis
- **Dumbbell Bicep Curls**: Arm movement tracking

### Excluded Exercises (Future Scope)
- **Cycling**: Requires different analysis approach (leg-focused motion detection)

### Auto-Detection Strategy
- Use pose estimation to identify exercise type based on movement patterns
- Fallback to manual classification if confidence is low

## 4. Data Models

### User Profile
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    weight_kg DECIMAL(5,2) NOT NULL,
    height_cm INTEGER NOT NULL,
    age INTEGER NOT NULL,
    gender VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Exercise Sessions
```sql
CREATE TABLE exercise_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    video_s3_key VARCHAR(500) NOT NULL,
    video_duration_seconds INTEGER,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'processing', -- processing, completed, failed
    raw_analysis JSONB,
    coaching_feedback JSONB,
    calories_burned DECIMAL(6,2),
    exercise_type VARCHAR(50),
    repetitions INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Analysis Results Schema (JSONB)
```json
{
  "exercise_type": "push_ups",
  "confidence": 0.95,
  "duration_seconds": 45,
  "repetitions": 15,
  "form_analysis": {
    "overall_score": 8.5,
    "key_angles": {
      "elbow_angle_range": [90, 180],
      "hip_alignment": "good"
    },
    "form_issues": ["slight hip sag at rep 8-10"]
  },
  "calories_burned": 12.5,
  "coaching_feedback": {
    "score": 8.5,
    "strengths": ["Good form overall", "Consistent tempo"],
    "improvements": ["Keep hips aligned throughout movement"],
    "recommendations": ["Try 3 sets of 12 for better muscle endurance"]
  },
  "pose_landmarks": [...], // Raw MediaPipe data
  "processing_metadata": {
    "frames_analyzed": 675,
    "confidence_scores": [0.95, 0.92, ...],
    "processing_time_seconds": 23.4
  }
}
```

## 5. Technical Implementation

### Lambda Function Structure
```
exercise_analysis_lambda/
├── lambda_function.py          # Main handler
├── video_processor.py          # Video processing logic
├── pose_analyzer.py           # MediaPipe integration
├── exercise_detector.py       # Exercise type detection
├── calorie_calculator.py      # MET-based calorie calculation
├── coaching_assistant.py      # OpenAI integration
├── database.py               # PostgreSQL operations
├── s3_client.py              # S3 download utilities
└── requirements.txt          # Dependencies
```

### Key Dependencies
```
mediapipe>=0.10.0
opencv-python>=4.8.0
openai>=1.0.0
psycopg2-binary>=2.9.0
boto3>=1.26.0
numpy>=1.24.0
```

### MET Values for Calorie Calculation
- Push-ups: 8.0 METs
- Rowing (vigorous): 8.5 METs
- Weight training (vigorous): 6.0 METs

### Calorie Formula
```
calories = MET × weight_kg × (duration_hours)
```

## 6. Processing Pipeline

### Step 1: Video Download & Validation
- Download MP4 from S3
- Validate video format and duration (10s - 5min)
- Extract basic metadata

### Step 2: Pose Estimation
- Extract frames at 10 FPS for analysis
- Run MediaPipe pose detection
- Filter low-confidence frames

### Step 3: Exercise Detection
- Analyze movement patterns
- Classify exercise type
- Return confidence score

### Step 4: Form Analysis
- Count repetitions
- Analyze key joint angles
- Identify form issues

### Step 5: Calorie Calculation
- Use MET values and user profile
- Calculate total calories burned

### Step 6: AI Coaching
- Format analysis data for OpenAI
- Request coaching feedback
- Parse and structure response

### Step 7: Data Persistence
- Save results to PostgreSQL
- Update session status
- Log metrics

## 7. Error Handling & Monitoring

### Error Categories
1. **Video Processing Errors**: Corrupt files, unsupported formats
2. **Pose Detection Failures**: Poor lighting, partial body visibility
3. **API Failures**: OpenAI rate limits, network issues
4. **Database Errors**: Connection issues, constraint violations

### Retry Strategy
- Single retry for transient failures
- Dead letter queue for permanent failures
- CloudWatch logging for all errors

### Monitoring & Logging
- CloudWatch metrics for processing time, success rate
- Detailed logging with correlation IDs
- Cost tracking for OpenAI API usage

## 8. MVP Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Lambda function setup
- [ ] S3 video download functionality
- [ ] PostgreSQL connection and basic models
- [ ] MediaPipe integration
- [ ] Basic push-up detection

### Phase 2: Exercise Analysis (Week 2)
- [ ] Exercise type auto-detection
- [ ] Rep counting for all supported exercises
- [ ] Form analysis algorithms
- [ ] Calorie calculation

### Phase 3: AI Coaching (Week 3)
- [ ] OpenAI API integration
- [ ] Prompt engineering for exercise coaching
- [ ] Response parsing and structuring

### Phase 4: Polish & Testing (Week 4)
- [ ] Error handling and retries
- [ ] Comprehensive logging
- [ ] Performance optimization
- [ ] End-to-end testing

## 9. Future Enhancements (Post-MVP)

### Advanced Features
- Trend analysis and progress tracking
- Real-time video analysis
- Mobile app integration
- Additional exercise types (cycling, yoga)
- Comparative analysis with fitness standards

### Technical Improvements
- Model optimization for faster processing
- Custom ML models for exercise-specific analysis
- Video preprocessing for better accuracy
- Caching layer for repeated analysis

## 10. Success Metrics

### Technical KPIs
- Processing time: < 5 minutes per video
- Accuracy: > 90% exercise type detection
- Uptime: > 99% availability
- Error rate: < 5%

### User Experience KPIs
- Actionable coaching feedback
- Accurate calorie estimates (±15% variance)
- Useful form analysis insights

## 11. Dependencies & Prerequisites

### AWS Resources (Existing)
- ✅ S3 bucket configured
- ✅ SNS topic setup
- ✅ SQS queue configured
- ✅ Lambda function created

### AWS Resources (To Be Created)
- [x] PostgreSQL Aurora cluster
- [x] CloudWatch log groups
- [x] IAM roles for database access

### External Services
- [ ] OpenAI API key configuration
- [ ] MediaPipe licensing (if required)

### User Data
- ✅ User profile data available
  - Weight: 73kg
  - Height: 5'10" (178cm)
  - Age: 39
  - Gender: Male

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Author**: AI Assistant  
**Review Status**: Ready for Implementation 