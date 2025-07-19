#!/usr/bin/env powershell
<#
.SYNOPSIS
    Deploy Exercise Tracker Lambda to ECR
    
.DESCRIPTION
    This script automates the process of building, tagging, and pushing 
    the Exercise Tracker Docker image to Amazon ECR.
    
    Steps performed:
    1. Build Docker image for linux/amd64 platform
    2. Tag image for ECR repository
    3. Authenticate Docker with ECR
    4. Push image to ECR repository
    
.EXAMPLE
    .\deploy-to-ecr.ps1
    
.NOTES
    Requirements:
    - Docker Desktop running
    - AWS CLI configured with appropriate permissions
    - ECR repository already created
#>

# Script configuration
$ErrorActionPreference = "Stop"
$ProgressPreference = "Continue"

# ECR Configuration
$ECR_REGION = "us-west-2"
$ECR_REGISTRY = "373275824940.dkr.ecr.us-west-2.amazonaws.com"
$ECR_REPOSITORY = "exercise-tracker-dev-pose-analysis"
$IMAGE_NAME = "exercise-tracker-dev-pose-analysis"
$ECR_URI = "$ECR_REGISTRY/$ECR_REPOSITORY"

# Color output functions
function Write-Step {
    param([string]$Message)
    Write-Host "`n[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "[NOTE] $Message" -ForegroundColor Yellow
}

# Main deployment function
function Deploy-ToECR {
    Write-Host "[DEPLOY] Starting ECR Deployment Process" -ForegroundColor Magenta
    Write-Host "=========================================" -ForegroundColor Magenta
    
    try {
        # Step 1: Build Docker Image
        Write-Step "Step 1/4: Building Docker image for linux/amd64 platform..."
        Write-Info "This may take 5-10 minutes for the first build..."
        
        docker build --platform linux/amd64 -t $IMAGE_NAME .
        
        if ($LASTEXITCODE -ne 0) {
            throw "Docker build failed with exit code $LASTEXITCODE"
        }
        Write-Success "Docker image built successfully"
        
        # Step 2: Tag Image for ECR
        Write-Step "Step 2/4: Tagging image for ECR repository..."
        
        docker tag "${IMAGE_NAME}:latest" "${ECR_URI}:latest"
        
        if ($LASTEXITCODE -ne 0) {
            throw "Docker tag failed with exit code $LASTEXITCODE"
        }
        Write-Success "Image tagged for ECR: ${ECR_URI}:latest"
        
        # Step 3: Authenticate with ECR
        Write-Step "Step 3/4: Authenticating Docker with ECR..."
        
        $loginPassword = aws ecr get-login-password --region $ECR_REGION
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to get ECR login password"
        }
        
        $loginPassword | docker login --username AWS --password-stdin $ECR_REGISTRY
        if ($LASTEXITCODE -ne 0) {
            throw "Docker login to ECR failed"
        }
        Write-Success "Successfully authenticated with ECR"
        
        # Step 4: Push Image to ECR
        Write-Step "Step 4/4: Pushing image to ECR repository..."
        Write-Info "This may take 2-5 minutes depending on your internet speed..."
        
        docker push "${ECR_URI}:latest"
        
        if ($LASTEXITCODE -ne 0) {
            throw "Docker push failed with exit code $LASTEXITCODE"
        }
        Write-Success "Image successfully pushed to ECR"
        
        # Success Summary
        Write-Host "`n[SUCCESS] Deployment Complete!" -ForegroundColor Green
        Write-Host "=============================" -ForegroundColor Green
        Write-Host "[SUCCESS] Image URI: ${ECR_URI}:latest" -ForegroundColor White
        Write-Host "[SUCCESS] Ready for Lambda function update" -ForegroundColor White
        
        Write-Host "`n[NEXT] Next Steps:" -ForegroundColor Yellow
        Write-Host "Run this command to update your Lambda function:" -ForegroundColor White
        Write-Host "aws lambda update-function-code --function-name exercise-tracker-dev-pose-analysis --image-uri ${ECR_URI}:latest --region $ECR_REGION" -ForegroundColor Gray
        
    }
    catch {
        Write-Error "Deployment failed: $($_.Exception.Message)"
        Write-Host "`n[HELP] Troubleshooting Tips:" -ForegroundColor Yellow
        Write-Host "- Ensure Docker Desktop is running" -ForegroundColor White
        Write-Host "- Verify AWS CLI is configured with ECR permissions" -ForegroundColor White
        Write-Host "- Check that the ECR repository exists" -ForegroundColor White
        Write-Host "- Ensure you have internet connectivity for pushing" -ForegroundColor White
        exit 1
    }
}

# Pre-flight checks
function Test-Prerequisites {
    Write-Step "Performing pre-flight checks..."
    
    # Check if Docker is running
    try {
        docker version | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Docker is not running"
        }
        Write-Success "Docker is running"
    }
    catch {
        Write-Error "Docker is not available or not running. Please start Docker Desktop."
        exit 1
    }
    
    # Check if AWS CLI is available
    try {
        aws --version | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "AWS CLI is not available"
        }
        Write-Success "AWS CLI is available"
    }
    catch {
        Write-Error "AWS CLI is not installed or not in PATH"
        exit 1
    }
    
    # Check if we're in the right directory (Dockerfile exists)
    if (-not (Test-Path "Dockerfile")) {
        Write-Error "Dockerfile not found. Please run this script from the project root directory."
        exit 1
    }
    Write-Success "Dockerfile found"
    
    Write-Success "All pre-flight checks passed"
}

# Main execution
Write-Host "Exercise Tracker - ECR Deployment Script" -ForegroundColor Magenta
Write-Host "=========================================" -ForegroundColor Magenta

Test-Prerequisites
Deploy-ToECR

Write-Host "`n[DONE] Script completed successfully!" -ForegroundColor Green 