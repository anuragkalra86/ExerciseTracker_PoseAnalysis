# ============================================================================
# Exercise Analysis Lambda - Docker Container Configuration
# ============================================================================
# This Dockerfile creates a Lambda container image that can run both:
# 1. As an AWS Lambda function in the cloud
# 2. As a local development environment for debugging
#
# Design Decisions:
# - Use official AWS Lambda Python base image for compatibility
# - Install system dependencies for OpenCV (requires native libraries)
# - Optimize for both functionality and image size
# - Support local development with proper environment setup
# ============================================================================

# Use AWS Lambda Python 3.13 base image
# Why: This ensures 100% compatibility with Lambda runtime environment
# Alternative: python:3.13-slim + manual Lambda runtime setup (more complex)
FROM public.ecr.aws/lambda/python:3.13

# ============================================================================
# SYSTEM DEPENDENCIES INSTALLATION
# ============================================================================
# Install system-level dependencies required for OpenCV and video processing
# These are native libraries that can't be installed via pip

# Update package manager and install build tools
# Why: OpenCV requires compilation of some native components
RUN dnf update -y && \
    dnf install -y \
        # Core build tools
        gcc gcc-c++ make cmake \
        # Version control (useful for development)
        git \
        # Network utilities for downloading packages
        wget \
        # Archive handling
        unzip zip \
        # Python development headers (required for some packages)
        python3-devel \
        # Image processing libraries (OpenCV dependencies)
        libjpeg-turbo-devel \
        libpng-devel \
        libtiff-devel \
        # Clean up package cache to reduce image size
    && dnf clean all \
    && rm -rf /var/cache/dnf

# ============================================================================
# APPLICATION SETUP
# ============================================================================

# Set the working directory
# This is where our application code will live
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements first (Docker layer caching optimization)
# Why: Dependencies change less frequently than source code
# This allows Docker to cache the pip install step
COPY requirements.txt .

# Install Python dependencies
# Design decisions:
# --no-cache-dir: Don't store pip cache (reduces image size)
# --upgrade: Ensure we get latest compatible versions
# --no-deps for critical packages: Avoid dependency conflicts
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# APPLICATION CODE
# ============================================================================

# Copy application source code
# Why separate COPY: Allows rebuilding only when source changes
COPY lambda_function.py .
COPY s3_client.py .
COPY video_processor.py .
COPY local_runner.py .
COPY config.py .

# Copy configuration and test files
COPY mock_events/ ./mock_events/
COPY README.md .

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

# Set environment variables for application
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}:${PYTHONPATH}"
ENV PYTHONUNBUFFERED=1

# Environment variable to detect we're running in a container
# This helps our application code detect the environment
ENV RUNNING_IN_CONTAINER=true

# Set default region (can be overridden at runtime)
ENV AWS_DEFAULT_REGION=us-west-2

# ============================================================================
# RUNTIME CONFIGURATION
# ============================================================================

# The CMD instruction specifies the Lambda handler
# Format: filename.function_name
# This can be overridden when running locally for development
CMD ["lambda_function.lambda_handler"]

# ============================================================================
# IMAGE METADATA
# ============================================================================
LABEL maintainer="Exercise Analysis Team"
LABEL version="1.0"
LABEL description="Exercise video analysis Lambda function with OpenCV"
LABEL phase="1-container-setup"

# Document the ports (for local development)
# Lambda doesn't use ports, but useful when running locally
EXPOSE 8080

# ============================================================================
# DEVELOPMENT NOTES
# ============================================================================
# Local Development Usage:
# 1. Build: docker build -t exercise-analysis .
# 2. Run locally: docker run -p 8080:8080 exercise-analysis
# 3. Test with mock events: docker run exercise-analysis python local_runner.py
# 4. Interactive debugging: docker run -it exercise-analysis /bin/bash
#
# Lambda Deployment:
# 1. Tag for ECR: docker tag exercise-analysis:latest <ECR-URI>:latest
# 2. Push to ECR: docker push <ECR-URI>:latest
# 3. Update Lambda function to use container image
# ============================================================================ 