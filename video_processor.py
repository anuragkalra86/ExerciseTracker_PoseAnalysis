"""
Video processor for exercise video analysis
Handles video validation and metadata extraction
"""

import logging
import os
import cv2
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class VideoProcessor:
    """
    Video processor for validation and metadata extraction
    """
    
    def __init__(self):
        """
        Initialize video processor
        """
        logger.info("Initialized VideoProcessor")
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from video file
        
        Args:
            file_path: Path to video file
            
        Returns:
            dict: Video metadata including duration, resolution, fps, codec, etc.
            
        Raises:
            Exception: If video cannot be processed
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")
        
        logger.info(f"Extracting metadata from video: {file_path}")
        
        # Initialize video capture
        cap = cv2.VideoCapture(file_path)
        
        try:
            if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {file_path}")
            
            # Get basic video properties
            metadata = self._extract_basic_properties(cap, file_path)
            
            # Validate video can be read
            metadata['is_valid_video'] = self._validate_video_readability(cap)
            
            logger.info(f"Successfully extracted metadata: {metadata}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting video metadata: {str(e)}")
            raise e
        finally:
            cap.release()
    
    def _extract_basic_properties(self, cap: cv2.VideoCapture, file_path: str) -> Dict[str, Any]:
        """
        Extract basic video properties using OpenCV
        
        Args:
            cap: OpenCV VideoCapture object
            file_path: Path to video file
            
        Returns:
            dict: Basic video properties
        """
        try:
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Calculate duration
            if fps > 0:
                duration_seconds = frame_count / fps
            else:
                duration_seconds = 0
            
            # Get file size
            file_size_bytes = os.path.getsize(file_path)
            
            # Get codec information (if available)
            fourcc = cap.get(cv2.CAP_PROP_FOURCC)
            codec = self._fourcc_to_string(fourcc) if fourcc else "unknown"
            
            metadata = {
                'duration_seconds': round(duration_seconds, 2),
                'fps': round(fps, 2),
                'frame_count': frame_count,
                'width': width,
                'height': height,
                'resolution': f"{width}x{height}",
                'file_size_bytes': file_size_bytes,
                'file_size_mb': round(file_size_bytes / (1024 * 1024), 2),
                'codec': codec,
                'aspect_ratio': round(width / height, 2) if height > 0 else 0,
                'total_pixels': width * height,
                'filename': os.path.basename(file_path)
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting basic video properties: {str(e)}")
            raise e
    
    def _validate_video_readability(self, cap: cv2.VideoCapture) -> bool:
        """
        Validate that the video can actually be read frame by frame
        
        Args:
            cap: OpenCV VideoCapture object
            
        Returns:
            bool: True if video is readable, False otherwise
        """
        try:
            # Try to read the first few frames to ensure video is not corrupted
            frames_to_test = 5
            frames_read = 0
            
            # Reset to beginning
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            for i in range(frames_to_test):
                ret, frame = cap.read()
                if ret and frame is not None:
                    frames_read += 1
                else:
                    break
            
            # Reset position back to beginning
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            # Consider video valid if we can read at least 1 frame
            is_valid = frames_read > 0
            
            logger.info(f"Video readability test: {frames_read}/{frames_to_test} frames read, valid: {is_valid}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating video readability: {str(e)}")
            return False
    
    def _fourcc_to_string(self, fourcc: float) -> str:
        """
        Convert FourCC code to readable string
        
        Args:
            fourcc: FourCC code from OpenCV
            
        Returns:
            str: Human-readable codec name
        """
        try:
            # Convert float to int and then to bytes
            fourcc_int = int(fourcc)
            fourcc_bytes = fourcc_int.to_bytes(4, byteorder='little')
            # Decode to string, handling potential encoding issues
            codec = fourcc_bytes.decode('ascii', errors='ignore').strip('\x00')
            return codec if codec else "unknown"
        except Exception:
            return "unknown"
    
    def extract_sample_frames(self, file_path: str, num_frames: int = 3) -> list:
        """
        Extract sample frames from video for preview/debugging
        
        Args:
            file_path: Path to video file
            num_frames: Number of frames to extract
            
        Returns:
            list: List of frame arrays (BGR format)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")
        
        logger.info(f"Extracting {num_frames} sample frames from video")
        
        cap = cv2.VideoCapture(file_path)
        frames = []
        
        try:
            if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {file_path}")
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames <= 0:
                logger.warning("Video has no frames")
                return frames
            
            # Calculate frame positions to extract evenly distributed frames
            if num_frames >= total_frames:
                frame_positions = list(range(total_frames))
            else:
                step = total_frames // num_frames
                frame_positions = [i * step for i in range(num_frames)]
            
            for position in frame_positions:
                cap.set(cv2.CAP_PROP_POS_FRAMES, position)
                ret, frame = cap.read()
                
                if ret and frame is not None:
                    frames.append(frame)
                    logger.debug(f"Extracted frame at position {position}")
                else:
                    logger.warning(f"Failed to extract frame at position {position}")
            
            logger.info(f"Successfully extracted {len(frames)} sample frames")
            return frames
            
        except Exception as e:
            logger.error(f"Error extracting sample frames: {str(e)}")
            raise e
        finally:
            cap.release()
    
    def get_video_quality_info(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze video quality metrics
        
        Args:
            file_path: Path to video file
            
        Returns:
            dict: Quality analysis results
        """
        try:
            metadata = self.extract_metadata(file_path)
            
            quality_info = {
                'resolution_category': self._categorize_resolution(metadata['width'], metadata['height']),
                'is_hd': metadata['height'] >= 720,
                'is_full_hd': metadata['height'] >= 1080,
                'fps_category': self._categorize_fps(metadata['fps']),
                'file_efficiency': self._calculate_file_efficiency(metadata),
                'estimated_bitrate_kbps': self._estimate_bitrate(metadata)
            }
            
            return quality_info
            
        except Exception as e:
            logger.error(f"Error analyzing video quality: {str(e)}")
            raise e
    
    def _categorize_resolution(self, width: int, height: int) -> str:
        """Categorize video resolution"""
        if height >= 2160:
            return "4K"
        elif height >= 1440:
            return "1440p"
        elif height >= 1080:
            return "1080p"
        elif height >= 720:
            return "720p"
        elif height >= 480:
            return "480p"
        else:
            return "low_res"
    
    def _categorize_fps(self, fps: float) -> str:
        """Categorize video frame rate"""
        if fps >= 60:
            return "high_fps"
        elif fps >= 30:
            return "standard_fps"
        elif fps >= 24:
            return "cinematic_fps"
        else:
            return "low_fps"
    
    def _calculate_file_efficiency(self, metadata: Dict[str, Any]) -> float:
        """Calculate file size efficiency (MB per minute)"""
        if metadata['duration_seconds'] > 0:
            return round(metadata['file_size_mb'] / (metadata['duration_seconds'] / 60), 2)
        return 0
    
    def _estimate_bitrate(self, metadata: Dict[str, Any]) -> int:
        """Estimate video bitrate in kbps"""
        if metadata['duration_seconds'] > 0:
            bits = metadata['file_size_bytes'] * 8
            bitrate_bps = bits / metadata['duration_seconds']
            return int(bitrate_bps / 1000)  # Convert to kbps
        return 0 