#!/usr/bin/env python3
"""
Configuration Management for Exercise Analysis
==============================================

This module provides centralized configuration management that adapts to different
execution environments (Lambda, Local, Container) and provides appropriate settings
for each context.

Design Philosophy:
- Environment-aware configuration
- Secure default values
- Easy local development overrides
- Validation and error checking
- Documentation for all settings

Usage:
    from config import get_config
    
    config = get_config()
    max_file_size = config.MAX_VIDEO_SIZE_MB
    s3_bucket = config.S3_BUCKET_NAME
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

# Get logger for this module
logger = logging.getLogger(__name__)

@dataclass
class ExerciseAnalysisConfig:
    """
    Configuration class for Exercise Analysis application
    
    This class holds all configuration values and provides environment-aware
    defaults with validation and documentation.
    """
    
    # ========================================================================
    # VIDEO PROCESSING CONFIGURATION
    # ========================================================================
    
    MAX_VIDEO_SIZE_MB: int = 500
    """Maximum allowed video file size in MB"""
    
    MIN_DURATION_SECONDS: int = 10
    """Minimum video duration in seconds"""
    
    MAX_DURATION_SECONDS: int = 300  # 5 minutes
    """Maximum video duration in seconds"""
    
    SUPPORTED_VIDEO_FORMATS: list = field(default_factory=lambda: ['.mp4', '.mov', '.avi'])
    """List of supported video file extensions"""
    
    VIDEO_PROCESSING_FPS: int = 10
    """Frame rate for video analysis (frames per second)"""
    
    # ========================================================================
    # AWS CONFIGURATION
    # ========================================================================
    
    AWS_REGION: str = "us-west-2"
    """AWS region for all services"""
    
    S3_BUCKET_NAME: str = "exercise-tracker-fa20651d-064c-4a95-8540-edfe2af691cd"
    """S3 bucket name for video storage"""
    
    SNS_TOPIC_ARN: str = "arn:aws:sns:us-west-2:373275824940:exercise-tracker-dev-video-upload-notifications"
    """SNS topic ARN for video upload notifications"""
    
    SQS_QUEUE_NAME: str = "exercise-tracker-dev-pose-analysis"
    """SQS queue name for processing messages"""
    
    DB_SECRET_NAME: str = "exercise-tracker/dev/aurora/connection-string"
    """AWS Secrets Manager secret name for database connection"""
    
    # ========================================================================
    # LAMBDA CONFIGURATION
    # ========================================================================
    
    LAMBDA_TIMEOUT_SECONDS: int = 900  # 15 minutes
    """Lambda function timeout in seconds"""
    
    LAMBDA_MEMORY_MB: int = 1024
    """Lambda function memory allocation in MB"""
    
    LAMBDA_TEMP_DIR: str = "/tmp"
    """Lambda temporary directory for file processing"""
    
    # ========================================================================
    # LOCAL DEVELOPMENT CONFIGURATION
    # ========================================================================
    
    LOCAL_TEMP_DIR: str = "./temp"
    """Local temporary directory for file processing"""
    
    LOCAL_VIDEO_DIR: str = "./test_videos"
    """Local directory for test video files"""
    
    LOCAL_OUTPUT_DIR: str = "./output"
    """Local directory for output files"""
    
    LOCAL_LOG_LEVEL: str = "DEBUG"
    """Log level for local development"""
    
    LOCAL_LOG_FILE: Optional[str] = "./logs/exercise_analysis.log"
    """Local log file path (None for console only)"""
    
    # ========================================================================
    # EXERCISE ANALYSIS CONFIGURATION
    # ========================================================================
    
    SUPPORTED_EXERCISES: list = field(default_factory=lambda: [
        "push_ups",
        "rowing", 
        "dumbbell_side_lateral_raises",
        "dumbbell_bicep_curls"
    ])
    """List of supported exercise types for analysis"""
    
    POSE_CONFIDENCE_THRESHOLD: float = 0.5
    """Minimum confidence threshold for pose detection"""
    
    REP_COUNTING_SMOOTHING_WINDOW: int = 5
    """Smoothing window size for repetition counting"""
    
    # ========================================================================
    # CALORIE CALCULATION CONFIGURATION
    # ========================================================================
    
    MET_VALUES: dict = field(default_factory=lambda: {
        "push_ups": 8.0,
        "rowing": 8.5,
        "dumbbell_side_lateral_raises": 6.0,
        "dumbbell_bicep_curls": 6.0
    })
    """MET (Metabolic Equivalent) values for different exercises"""
    
    DEFAULT_USER_WEIGHT_KG: float = 73.0
    """Default user weight for calorie calculations (your weight)"""
    
    DEFAULT_USER_HEIGHT_CM: int = 178  # 5'10"
    """Default user height in centimeters"""
    
    DEFAULT_USER_AGE: int = 39
    """Default user age"""
    
    DEFAULT_USER_GENDER: str = "male"
    """Default user gender"""
    
    # ========================================================================
    # API CONFIGURATION
    # ========================================================================
    
    OPENAI_API_TIMEOUT_SECONDS: int = 30
    """Timeout for OpenAI API calls in seconds"""
    
    OPENAI_MAX_RETRIES: int = 3
    """Maximum number of retries for OpenAI API calls"""
    
    OPENAI_MODEL: str = "gpt-4o-mini"
    """OpenAI model to use for coaching feedback"""
    
    # ========================================================================
    # PERFORMANCE AND MONITORING
    # ========================================================================
    
    ENABLE_PERFORMANCE_MONITORING: bool = True
    """Enable detailed performance monitoring and timing"""
    
    ENABLE_DETAILED_LOGGING: bool = True
    """Enable detailed logging throughout the application"""
    
    MAX_CONCURRENT_PROCESSES: int = 3
    """Maximum number of concurrent video processing tasks"""
    
    CLEANUP_TEMP_FILES: bool = True
    """Automatically cleanup temporary files after processing"""
    
    # ========================================================================
    # DEVELOPMENT AND TESTING
    # ========================================================================
    
    MOCK_EXTERNAL_APIS: bool = False
    """Use mock implementations for external APIs (testing)"""
    
    SAVE_DEBUG_FRAMES: bool = False
    """Save intermediate processing frames for debugging"""
    
    DEBUG_OUTPUT_DIR: str = "./debug_output"
    """Directory for debug output files"""
    
    ENABLE_PROFILING: bool = False
    """Enable performance profiling for optimization"""

def detect_execution_environment() -> str:
    """
    Detect the current execution environment
    
    Returns:
        str: Environment type ('lambda', 'container', 'local')
    """
    # Check for AWS Lambda environment
    if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
        return 'lambda'
    
    # Check for container environment
    if os.getenv('RUNNING_IN_CONTAINER', 'false').lower() == 'true':
        return 'container'
    
    # Default to local environment
    return 'local'

def apply_environment_overrides(config: ExerciseAnalysisConfig, environment: str) -> None:
    """
    Apply environment-specific configuration overrides
    
    Args:
        config: Configuration object to modify
        environment: Environment type ('lambda', 'container', 'local')
    """
    if environment == 'lambda':
        # Lambda-specific overrides
        config.LOCAL_LOG_LEVEL = "INFO"  # Less verbose in Lambda
        config.CLEANUP_TEMP_FILES = True  # Always cleanup in Lambda
        config.SAVE_DEBUG_FRAMES = False  # No debug output in Lambda
        config.ENABLE_PROFILING = False  # No profiling in Lambda
        config.LOCAL_TEMP_DIR = config.LAMBDA_TEMP_DIR
        logger.info("Applied Lambda environment configuration overrides")
        
    elif environment == 'container':
        # Container-specific overrides
        config.LOCAL_LOG_LEVEL = "INFO"
        config.CLEANUP_TEMP_FILES = True
        config.LOCAL_TEMP_DIR = "/app/temp"  # Container temp directory
        logger.info("Applied Container environment configuration overrides")
        
    elif environment == 'local':
        # Local development overrides
        config.LOCAL_LOG_LEVEL = "DEBUG"  # Verbose logging for development
        config.SAVE_DEBUG_FRAMES = True   # Save debug output locally
        config.ENABLE_PROFILING = True    # Enable profiling for optimization
        config.CLEANUP_TEMP_FILES = False # Keep files for inspection
        logger.info("Applied Local development configuration overrides")

def apply_environment_variable_overrides(config: ExerciseAnalysisConfig) -> None:
    """
    Apply configuration overrides from environment variables
    
    This allows runtime configuration without code changes.
    Environment variables follow the pattern: EXERCISE_ANALYSIS_<SETTING_NAME>
    
    Args:
        config: Configuration object to modify
    """
    env_prefix = "EXERCISE_ANALYSIS_"
    
    # Mapping of environment variable suffixes to config attributes
    env_mappings = {
        "MAX_VIDEO_SIZE_MB": ("MAX_VIDEO_SIZE_MB", int),
        "MIN_DURATION_SECONDS": ("MIN_DURATION_SECONDS", int),
        "MAX_DURATION_SECONDS": ("MAX_DURATION_SECONDS", int),
        "AWS_REGION": ("AWS_REGION", str),
        "S3_BUCKET_NAME": ("S3_BUCKET_NAME", str),
        "LOG_LEVEL": ("LOCAL_LOG_LEVEL", str),
        "ENABLE_DEBUG": ("SAVE_DEBUG_FRAMES", lambda x: x.lower() == 'true'),
        "ENABLE_PROFILING": ("ENABLE_PROFILING", lambda x: x.lower() == 'true'),
        "USER_WEIGHT_KG": ("DEFAULT_USER_WEIGHT_KG", float),
        "USER_AGE": ("DEFAULT_USER_AGE", int),
    }
    
    overrides_applied = []
    
    for env_suffix, (attr_name, converter) in env_mappings.items():
        env_var_name = f"{env_prefix}{env_suffix}"
        env_value = os.getenv(env_var_name)
        
        if env_value is not None:
            try:
                converted_value = converter(env_value)
                setattr(config, attr_name, converted_value)
                overrides_applied.append(f"{attr_name}={converted_value}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid value for {env_var_name}: {env_value}. Error: {e}")
    
    if overrides_applied:
        logger.info(f"Applied environment variable overrides: {', '.join(overrides_applied)}")

def validate_configuration(config: ExerciseAnalysisConfig) -> None:
    """
    Validate configuration values and log warnings for potential issues
    
    Args:
        config: Configuration object to validate
    """
    warnings = []
    
    # Validate video processing settings
    if config.MAX_VIDEO_SIZE_MB > 1000:
        warnings.append(f"MAX_VIDEO_SIZE_MB ({config.MAX_VIDEO_SIZE_MB}) is very large")
    
    if config.MIN_DURATION_SECONDS >= config.MAX_DURATION_SECONDS:
        warnings.append("MIN_DURATION_SECONDS must be less than MAX_DURATION_SECONDS")
    
    # Validate AWS settings
    if not config.S3_BUCKET_NAME:
        warnings.append("S3_BUCKET_NAME is empty")
    
    # Validate exercise settings
    if config.POSE_CONFIDENCE_THRESHOLD < 0.1 or config.POSE_CONFIDENCE_THRESHOLD > 1.0:
        warnings.append(f"POSE_CONFIDENCE_THRESHOLD ({config.POSE_CONFIDENCE_THRESHOLD}) should be between 0.1 and 1.0")
    
    # Validate user settings
    if config.DEFAULT_USER_WEIGHT_KG <= 0:
        warnings.append("DEFAULT_USER_WEIGHT_KG must be positive")
    
    # Log warnings
    for warning in warnings:
        logger.warning(f"Configuration warning: {warning}")
    
    if not warnings:
        logger.info("Configuration validation passed")

def setup_local_directories(config: ExerciseAnalysisConfig) -> None:
    """
    Create necessary local directories for development
    
    Args:
        config: Configuration object with directory settings
    """
    directories_to_create = [
        config.LOCAL_TEMP_DIR,
        config.LOCAL_VIDEO_DIR,
        config.LOCAL_OUTPUT_DIR,
        config.DEBUG_OUTPUT_DIR,
    ]
    
    # Add log directory if log file is specified
    if config.LOCAL_LOG_FILE:
        log_dir = Path(config.LOCAL_LOG_FILE).parent
        directories_to_create.append(str(log_dir))
    
    created_dirs = []
    for directory in directories_to_create:
        dir_path = Path(directory)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(directory)
            except OSError as e:
                logger.warning(f"Could not create directory {directory}: {e}")
    
    if created_dirs:
        logger.info(f"Created local directories: {', '.join(created_dirs)}")

# ============================================================================
# MAIN CONFIGURATION FACTORY
# ============================================================================

_config_instance: Optional[ExerciseAnalysisConfig] = None

def get_config(reload: bool = False) -> ExerciseAnalysisConfig:
    """
    Get the application configuration (singleton pattern)
    
    Args:
        reload: Force reload of configuration
        
    Returns:
        ExerciseAnalysisConfig: Configured application settings
    """
    global _config_instance
    
    if _config_instance is None or reload:
        logger.info("Initializing Exercise Analysis configuration...")
        
        # Create base configuration
        config = ExerciseAnalysisConfig()
        
        # Detect environment and apply overrides
        environment = detect_execution_environment()
        logger.info(f"Detected execution environment: {environment}")
        
        # Apply environment-specific overrides
        apply_environment_overrides(config, environment)
        
        # Apply environment variable overrides
        apply_environment_variable_overrides(config)
        
        # Validate configuration
        validate_configuration(config)
        
        # Setup local directories if in local environment
        if environment == 'local':
            setup_local_directories(config)
        
        # Store the instance
        _config_instance = config
        
        logger.info("Configuration initialization complete")
    
    return _config_instance

def print_configuration_summary(config: Optional[ExerciseAnalysisConfig] = None) -> None:
    """
    Print a summary of the current configuration
    
    Args:
        config: Configuration to summarize (uses current config if None)
    """
    if config is None:
        config = get_config()
    
    environment = detect_execution_environment()
    
    summary = f"""
🔧 Exercise Analysis Configuration Summary
=========================================
Environment: {environment.upper()}
AWS Region: {config.AWS_REGION}
S3 Bucket: {config.S3_BUCKET_NAME}

📹 Video Processing:
- Max size: {config.MAX_VIDEO_SIZE_MB}MB
- Duration: {config.MIN_DURATION_SECONDS}s - {config.MAX_DURATION_SECONDS}s
- Formats: {', '.join(config.SUPPORTED_VIDEO_FORMATS)}
- Processing FPS: {config.VIDEO_PROCESSING_FPS}

🏋️ Exercise Analysis:
- Supported: {', '.join(config.SUPPORTED_EXERCISES)}
- Pose confidence: {config.POSE_CONFIDENCE_THRESHOLD}
- Rep smoothing: {config.REP_COUNTING_SMOOTHING_WINDOW}

👤 User Profile:
- Weight: {config.DEFAULT_USER_WEIGHT_KG}kg
- Height: {config.DEFAULT_USER_HEIGHT_CM}cm
- Age: {config.DEFAULT_USER_AGE}
- Gender: {config.DEFAULT_USER_GENDER}

🔧 Development:
- Log level: {config.LOCAL_LOG_LEVEL}
- Debug frames: {'Yes' if config.SAVE_DEBUG_FRAMES else 'No'}
- Profiling: {'Yes' if config.ENABLE_PROFILING else 'No'}
- Temp dir: {config.LOCAL_TEMP_DIR}
=========================================
    """
    
    print(summary)

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def is_development_mode() -> bool:
    """Check if running in development mode"""
    return detect_execution_environment() == 'local'

def get_temp_directory() -> str:
    """Get appropriate temporary directory for current environment"""
    config = get_config()
    return config.LOCAL_TEMP_DIR

def get_supported_exercises() -> list:
    """Get list of supported exercise types"""
    config = get_config()
    return config.SUPPORTED_EXERCISES.copy()

def get_met_value(exercise_type: str) -> float:
    """Get MET value for a specific exercise type"""
    config = get_config()
    return config.MET_VALUES.get(exercise_type, 6.0)  # Default MET value

if __name__ == "__main__":
    # When run directly, print configuration summary
    print_configuration_summary() 