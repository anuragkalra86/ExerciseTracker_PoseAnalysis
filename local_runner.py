#!/usr/bin/env python3
"""
Local Development Runner for Exercise Analysis
==============================================

This module provides advanced local development utilities beyond the basic
lambda_function.py local execution. It includes:

1. Batch processing capabilities
2. Development server simulation
3. Test data generation
4. Performance profiling
5. Mock AWS service integration

Design Philosophy:
- Separate development concerns from production Lambda code
- Provide rich debugging and testing capabilities
- Simulate AWS environment as closely as possible locally
- Enable rapid development iteration

Usage Examples:
- Development server: python local_runner.py server
- Batch process videos: python local_runner.py batch --directory /videos
- Generate test data: python local_runner.py generate-test-data
- Profile performance: python local_runner.py profile --video test.mp4
"""

import asyncio
import json
import logging
import os
import sys
import time
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
import traceback

# Import our main application modules
from lambda_function import (
    lambda_handler, 
    create_mock_context, 
    create_mock_sqs_event,
    process_local_video_file,
    setup_logging,
    is_lambda_environment,
    is_container_environment
)

# Initialize logging
logger = setup_logging()

class LocalDevelopmentServer:
    """
    Local development server that simulates AWS Lambda execution environment
    """
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.request_count = 0
        
    def simulate_lambda_invocation(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate a Lambda invocation with timing and monitoring
        
        Args:
            event: Lambda event payload
            
        Returns:
            dict: Response with execution metrics
        """
        self.request_count += 1
        invocation_id = f"local-{self.request_count:04d}"
        
        logger.info(f"=== LAMBDA INVOCATION {invocation_id} ===")
        start_time = time.time()
        
        try:
            # Create mock context
            context = create_mock_context(invocation_id)
            
            # Execute the handler
            result = lambda_handler(event, context)
            
            # Calculate execution metrics
            execution_time = time.time() - start_time
            
            # Log execution summary
            logger.info(f"Invocation {invocation_id} completed successfully")
            logger.info(f"Execution time: {execution_time:.2f} seconds")
            
            # Add execution metadata to response
            result['execution_metadata'] = {
                'invocation_id': invocation_id,
                'execution_time_seconds': round(execution_time, 2),
                'memory_used_mb': 'simulated',  # In real Lambda, this comes from CloudWatch
                'billed_duration_ms': int(execution_time * 1000)
            }
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_details = {
                'invocation_id': invocation_id,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'execution_time_seconds': round(execution_time, 2),
                'traceback': traceback.format_exc()
            }
            
            logger.error(f"Invocation {invocation_id} failed: {str(e)}")
            logger.error(f"Execution time: {execution_time:.2f} seconds")
            
            return {
                'statusCode': 500,
                'error': error_details,
                'message': 'Lambda invocation failed'
            }
    
    def start_interactive_server(self):
        """
        Start an interactive development server for testing
        """
        logger.info(f"🚀 Starting Exercise Analysis Development Server")
        logger.info(f"📍 Environment: {'Container' if is_container_environment() else 'Native'}")
        logger.info(f"🔧 Interactive mode - Type commands to test the Lambda function")
        logger.info(f"💡 Type 'help' for available commands\n")
        
        while True:
            try:
                command = input("exercise-analysis> ").strip()
                
                if command.lower() in ['exit', 'quit', 'q']:
                    logger.info("Shutting down development server...")
                    break
                elif command.lower() == 'help':
                    self._show_help()
                elif command.lower() == 'status':
                    self._show_status()
                elif command.startswith('process-s3 '):
                    self._handle_s3_command(command)
                elif command.startswith('process-local '):
                    self._handle_local_command(command)
                elif command.lower() == 'generate-mock':
                    self._generate_mock_event()
                else:
                    logger.warning(f"Unknown command: {command}. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                logger.info("\nShutting down development server...")
                break
            except Exception as e:
                logger.error(f"Error executing command: {str(e)}")
    
    def _show_help(self):
        """Show available interactive commands"""
        help_text = """
Available Commands:
==================

🎥 Video Processing:
  process-local <path>                 Process a local video file
  process-s3 <bucket> <key>           Process video from S3
  
📊 Development Tools:
  generate-mock                       Generate sample mock event file
  status                             Show server status and statistics
  
🔧 System:
  help                               Show this help message
  exit, quit, q                      Shutdown the server

Examples:
  process-local /videos/pushups.mp4
  process-s3 my-bucket workout-video.mp4
  generate-mock
        """
        print(help_text)
    
    def _show_status(self):
        """Show server status"""
        status = f"""
🖥️  Development Server Status
============================
Requests processed: {self.request_count}
Environment: {'Lambda' if is_lambda_environment() else 'Local'}
Container: {'Yes' if is_container_environment() else 'No'}
Python version: {sys.version.split()[0]}
Working directory: {os.getcwd()}
        """
        print(status)
    
    def _handle_s3_command(self, command: str):
        """Handle process-s3 command"""
        parts = command.split()
        if len(parts) != 3:
            logger.error("Usage: process-s3 <bucket> <key>")
            return
        
        _, bucket, key = parts
        logger.info(f"Processing S3 file: s3://{bucket}/{key}")
        
        # Create mock SQS event and process
        mock_event = create_mock_sqs_event(bucket, key)
        result = self.simulate_lambda_invocation(mock_event)
        
        print(json.dumps(result, indent=2))
    
    def _handle_local_command(self, command: str):
        """Handle process-local command"""
        parts = command.split(maxsplit=1)
        if len(parts) != 2:
            logger.error("Usage: process-local <path>")
            return
        
        _, path = parts
        logger.info(f"Processing local file: {path}")
        
        result = process_local_video_file(path)
        print(json.dumps(result, indent=2))
    
    def _generate_mock_event(self):
        """Generate a sample mock event file"""
        mock_event = create_mock_sqs_event(
            "exercise-tracker-fa20651d-064c-4a95-8540-edfe2af691cd",
            "sample_workout.mp4"
        )
        
        output_file = "mock_events/generated_sample.json"
        os.makedirs("mock_events", exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(mock_event, f, indent=2)
        
        logger.info(f"Generated mock event file: {output_file}")

class BatchProcessor:
    """
    Batch processing utilities for development and testing
    """
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        
    def process_directory(self, directory: str, pattern: str = "*.mp4") -> List[Dict[str, Any]]:
        """
        Process all video files in a directory
        
        Args:
            directory: Directory containing video files
            pattern: File pattern to match (default: *.mp4)
            
        Returns:
            list: Processing results for each file
        """
        video_dir = Path(directory)
        if not video_dir.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        video_files = list(video_dir.glob(pattern))
        logger.info(f"Found {len(video_files)} video files in {directory}")
        
        if not video_files:
            logger.warning(f"No video files found matching pattern '{pattern}'")
            return []
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all processing tasks
            future_to_file = {
                executor.submit(process_local_video_file, str(video_file)): video_file
                for video_file in video_files
            }
            
            # Collect results as they complete
            for future in future_to_file:
                video_file = future_to_file[future]
                try:
                    result = future.result()
                    result['source_file'] = str(video_file)
                    results.append(result)
                    
                    status = "✅ SUCCESS" if result['statusCode'] == 200 else "❌ FAILED"
                    logger.info(f"{status} {video_file.name}")
                    
                except Exception as e:
                    error_result = {
                        'statusCode': 500,
                        'source_file': str(video_file),
                        'error': str(e),
                        'message': f'Failed to process {video_file.name}'
                    }
                    results.append(error_result)
                    logger.error(f"❌ FAILED {video_file.name}: {str(e)}")
        
        # Summary
        successful = sum(1 for r in results if r['statusCode'] == 200)
        failed = len(results) - successful
        
        logger.info(f"Batch processing complete: {successful} successful, {failed} failed")
        
        return results

class PerformanceProfiler:
    """
    Performance profiling utilities for optimization
    """
    
    @staticmethod
    def profile_video_processing(video_path: str, iterations: int = 5) -> Dict[str, Any]:
        """
        Profile video processing performance
        
        Args:
            video_path: Path to video file for profiling
            iterations: Number of iterations to run
            
        Returns:
            dict: Performance metrics
        """
        logger.info(f"Profiling video processing: {video_path} ({iterations} iterations)")
        
        execution_times = []
        memory_usage = []  # Placeholder for memory profiling
        
        for i in range(iterations):
            logger.info(f"Profiling iteration {i+1}/{iterations}")
            
            start_time = time.time()
            result = process_local_video_file(video_path)
            execution_time = time.time() - start_time
            
            execution_times.append(execution_time)
            
            if result['statusCode'] != 200:
                logger.warning(f"Iteration {i+1} failed: {result.get('error', 'Unknown error')}")
        
        # Calculate statistics
        avg_time = sum(execution_times) / len(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)
        
        profile_results = {
            'video_file': video_path,
            'iterations': iterations,
            'execution_times': execution_times,
            'statistics': {
                'average_time_seconds': round(avg_time, 3),
                'min_time_seconds': round(min_time, 3),
                'max_time_seconds': round(max_time, 3),
                'time_variance': round(max_time - min_time, 3)
            }
        }
        
        logger.info(f"Profiling complete - Average: {avg_time:.3f}s, Range: {min_time:.3f}s - {max_time:.3f}s")
        
        return profile_results

def main():
    """
    Main entry point for local development runner
    """
    parser = argparse.ArgumentParser(
        description="Exercise Analysis - Advanced Local Development Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Server command
    server_parser = subparsers.add_parser('server', help='Start interactive development server')
    server_parser.add_argument('--port', type=int, default=8080, help='Server port (default: 8080)')
    
    # Batch processing command
    batch_parser = subparsers.add_parser('batch', help='Batch process video files')
    batch_parser.add_argument('--directory', required=True, help='Directory containing video files')
    batch_parser.add_argument('--pattern', default='*.mp4', help='File pattern (default: *.mp4)')
    batch_parser.add_argument('--workers', type=int, default=3, help='Max concurrent workers (default: 3)')
    batch_parser.add_argument('--output', help='Output file for results (JSON format)')
    
    # Profile command
    profile_parser = subparsers.add_parser('profile', help='Profile performance')
    profile_parser.add_argument('--video', required=True, help='Video file to profile')
    profile_parser.add_argument('--iterations', type=int, default=5, help='Number of iterations (default: 5)')
    
    # Generate test data command
    test_parser = subparsers.add_parser('generate-test-data', help='Generate test data and mock events')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'server':
            server = LocalDevelopmentServer(args.port)
            server.start_interactive_server()
            
        elif args.command == 'batch':
            processor = BatchProcessor(args.workers)
            results = processor.process_directory(args.directory, args.pattern)
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
                logger.info(f"Results saved to: {args.output}")
            else:
                print(json.dumps(results, indent=2))
                
        elif args.command == 'profile':
            results = PerformanceProfiler.profile_video_processing(
                args.video, args.iterations
            )
            print(json.dumps(results, indent=2))
            
        elif args.command == 'generate-test-data':
            # Create mock events directory and sample files
            os.makedirs('mock_events', exist_ok=True)
            
            # Generate various mock events
            events = {
                'sample_s3_event.json': create_mock_sqs_event(
                    "exercise-tracker-fa20651d-064c-4a95-8540-edfe2af691cd",
                    "sample_workout.mp4"
                ),
                'pushup_video_event.json': create_mock_sqs_event(
                    "exercise-tracker-fa20651d-064c-4a95-8540-edfe2af691cd",
                    "exercises/pushups_session_1.mp4"
                ),
                'rowing_video_event.json': create_mock_sqs_event(
                    "exercise-tracker-fa20651d-064c-4a95-8540-edfe2af691cd",
                    "exercises/rowing_session_2.mp4"
                )
            }
            
            for filename, event in events.items():
                filepath = Path('mock_events') / filename
                with open(filepath, 'w') as f:
                    json.dump(event, f, indent=2)
                logger.info(f"Generated: {filepath}")
            
            logger.info("Test data generation complete!")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in local runner: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 