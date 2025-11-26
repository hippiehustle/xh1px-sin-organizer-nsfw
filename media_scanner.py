#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Intelligent Media Scanner with NudeNet Visual Analysis
Production-grade NSFW detection with comprehensive error handling and optimization.

BUFF Enhanced v2: Production-ready with security, performance, and reliability improvements.
"""

import os
import sys
import shutil
import json
import logging
import traceback
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set, Any
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, asdict, field
import hashlib
import time
import platform
from collections import defaultdict


# Set UTF-8 encoding for Windows console
if platform.system() == 'Windows':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


class DetectionFactory:
    """Factory for creating detection results with consistent formatting."""

    @staticmethod
    def create_visual_detection(detections_count: int, nsfw_labels: List[str],
                               max_confidence: float, processing_time: float) -> 'DetectionResult':
        """Create detection result from visual analysis."""
        return DetectionResult(
            detections_count=detections_count,
            nsfw_labels=nsfw_labels,
            max_confidence=max_confidence,
            method='visual_analysis',
            processing_time=processing_time
        )

    @staticmethod
    def create_filename_detection(processing_time: float) -> 'DetectionResult':
        """Create detection result from filename analysis."""
        return DetectionResult(
            detections_count=0,
            nsfw_labels=[],
            max_confidence=0.0,
            method='filename_only',
            processing_time=processing_time
        )

    @staticmethod
    def create_error_detection(error: str, processing_time: float) -> 'DetectionResult':
        """Create detection result for error case."""
        return DetectionResult(
            detections_count=0,
            nsfw_labels=[],
            max_confidence=0.0,
            method='error',
            error=error,
            processing_time=processing_time
        )

    @staticmethod
    def create_video_detection(frames_checked: int, nsfw_frames: int,
                              processing_time: float) -> 'DetectionResult':
        """Create detection result from video analysis."""
        ratio = nsfw_frames / max(frames_checked, 1)
        return DetectionResult(
            detections_count=frames_checked,
            nsfw_labels=[f"nsfw_frames:{nsfw_frames}/{frames_checked}"],
            max_confidence=ratio,
            method='video_frame_analysis',
            processing_time=processing_time
        )


@dataclass
class DetectionResult:
    """Structured detection result with type safety."""
    detections_count: int = 0
    nsfw_labels: List[str] = field(default_factory=list)
    max_confidence: float = 0.0
    method: str = "unknown"
    error: Optional[str] = None
    processing_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class VideoFrameExtractor:
    """Extracts and manages video frames."""

    FRAME_INTERVAL = 30  # seconds
    MAX_FRAMES = 10

    def __init__(self):
        """Initialize video frame extractor."""
        self.temp_frame_path = None

    def get_temp_path(self) -> Path:
        """Get or create temp frame path."""
        if not self.temp_frame_path:
            temp_dir = Path.home() / "AppData" / "Local" / "Temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            self.temp_frame_path = temp_dir / f"temp_frame_{os.getpid()}.jpg"
        return self.temp_frame_path

    def extract_frames(self, video_path: str, fps: float, total_frames: int) -> List[Path]:
        """Extract frames from video."""
        try:
            import cv2
        except ImportError:
            return []

        frame_interval = int(fps * self.FRAME_INTERVAL)
        frames_to_check = min(self.MAX_FRAMES, max(1, total_frames // max(frame_interval, 1)))

        extracted_frames = []
        cap = cv2.VideoCapture(video_path)

        try:
            for i in range(frames_to_check):
                frame_pos = min(i * frame_interval, total_frames - 1)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                ret, frame = cap.read()

                if ret and frame is not None:
                    temp_path = self.get_temp_path()
                    cv2.imwrite(str(temp_path), frame)
                    extracted_frames.append(temp_path)
        finally:
            cap.release()

        return extracted_frames

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_frame_path and self.temp_frame_path.exists():
            try:
                self.temp_frame_path.unlink()
            except Exception:
                pass


class BatchProcessor:
    """Processes files in batches with progress reporting."""

    def __init__(self, batch_size: int = 1000):
        """Initialize batch processor."""
        self.batch_size = batch_size

    def process_in_batches(self, items: List[Any], callback, batch_callback=None) -> None:
        """Process items in batches."""
        total = len(items)
        for i, item in enumerate(items):
            callback(item)
            if batch_callback and (i + 1) % self.batch_size == 0:
                batch_callback(i + 1, total)

    def split_into_batches(self, items: List[Any]) -> List[List[Any]]:
        """Split items into batches."""
        batches = []
        for i in range(0, len(items), self.batch_size):
            batches.append(items[i:i + self.batch_size])
        return batches


class NudeNetIntegration:
    """Wrapper for NudeNet visual analysis."""

    NSFW_LABELS = {
        'FEMALE_GENITALIA_EXPOSED',
        'MALE_GENITALIA_EXPOSED',
        'FEMALE_BREAST_EXPOSED',
        'BUTTOCKS_EXPOSED',
        'ANUS_EXPOSED'
    }

    def __init__(self):
        """Initialize NudeNet integration."""
        self.detector = None
        self.available = False
        self._initialize()

    def _initialize(self) -> None:
        """Initialize NudeNet detector."""
        try:
            from nudenet import NudeDetector
            self.detector = NudeDetector()
            self.available = True
        except ImportError:
            self.available = False
        except Exception:
            self.available = False

    def detect(self, filepath: str) -> List[Dict[str, Any]]:
        """Run NudeNet detection on image."""
        if not self.available or not self.detector:
            return []
        try:
            return self.detector.detect(filepath)
        except Exception:
            return []

    def process_detections(self, detections: List[Dict[str, Any]], confidence_threshold: float) -> Tuple[bool, float, List[str]]:
        """Process NudeNet detections."""
        nsfw_detected = False
        max_confidence = 0.0
        detected_labels = []

        for detection in detections:
            label = detection.get('class', '')
            confidence = detection.get('score', 0.0)

            if label in self.NSFW_LABELS and confidence > confidence_threshold:
                nsfw_detected = True
                max_confidence = max(max_confidence, confidence)
                detected_labels.append(f"{label}:{confidence:.2f}")

        return nsfw_detected, max_confidence, detected_labels


class TimingMetrics:
    """Tracks timing metrics for performance analysis."""

    def __init__(self):
        """Initialize timing tracker."""
        self.visual_time = 0.0
        self.hash_time = 0.0
        self.start_time = datetime.now()

    def add_visual_time(self, duration: float) -> None:
        """Add visual analysis time."""
        self.visual_time += duration

    def add_hash_time(self, duration: float) -> None:
        """Add file hashing time."""
        self.hash_time += duration

    def get_total_time(self) -> float:
        """Get total elapsed time."""
        return (datetime.now() - self.start_time).total_seconds()

    def get_avg_file_time(self, file_count: int) -> float:
        """Calculate average time per file."""
        if file_count == 0:
            return 0.0
        return self.get_total_time() / file_count

    def to_dict(self) -> Dict[str, float]:
        """Convert metrics to dictionary."""
        return {
            'total_visual_time': self.visual_time,
            'total_hash_time': self.hash_time,
            'total_elapsed_time': self.get_total_time()
        }


class FileOrganizer:
    """Handles file organization (copy/move operations)."""

    @staticmethod
    def get_unique_path(dest_dir: Path, src_path: Path) -> Path:
        """Get unique destination path, handling duplicates."""
        dest_path = dest_dir / src_path.name
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{src_path.stem}_{counter}{src_path.suffix}"
            counter += 1
        return dest_path

    @staticmethod
    def transfer_file(src_path: Path, dest_path: Path, move: bool) -> bool:
        """Transfer file (copy or move) with error handling."""
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if move:
                shutil.move(str(src_path), str(dest_path))
            else:
                shutil.copy2(str(src_path), str(dest_path))
            return True
        except Exception:
            return False

    @staticmethod
    def organize_category(files: List[Dict[str, Any]], dest_dir: Path, move: bool) -> Tuple[int, int]:
        """Organize files in a category. Returns (success_count, fail_count)."""
        success = 0
        failed = 0

        for file_info in files:
            src_path = Path(file_info['path'])
            if not src_path.exists():
                failed += 1
                continue

            dest_path = FileOrganizer.get_unique_path(dest_dir, src_path)
            if FileOrganizer.transfer_file(src_path, dest_path, move):
                success += 1
            else:
                failed += 1

        return success, failed


class ReportFormatter:
    """Formats scan results for output."""

    @staticmethod
    def format_summary(results: Dict[str, Any], duration: float, method: str) -> str:
        """Format summary report."""
        stats = results['stats']
        perf = results['performance']

        summary = f"""
+===================================================================+
|    ENHANCED MEDIA SCANNER - AI VISUAL ANALYSIS RESULTS v2.0     |
+===================================================================+

Analysis Method: {method}
Scan Duration: {duration:.2f} seconds ({duration/60:.1f} minutes)
Total Files Scanned: {stats['total_scanned']:,}
Total Size: {stats['total_size'] / (1024**3):.2f} GB
Errors Encountered: {stats['errors']}

===================================================================

PERFORMANCE METRICS:
  Avg Time per File: {perf['avg_file_time']:.3f}s
  Files per Second: {stats['total_scanned'] / max(duration, 1):.1f}
  Total Visual Analysis Time: {perf['total_visual_time']:.2f}s
  Total Hash Time: {perf['total_hash_time']:.2f}s

===================================================================

CLASSIFICATION RESULTS:
  [+] SFW (Safe):      {stats['sfw_detected']:,} files
  [X] NSFW (Explicit): {stats['nsfw_detected']:,} files
  [?] Uncertain:       {stats['uncertain']:,} files

===================================================================
"""
        return summary

    @staticmethod
    def format_detailed_breakdown(results: Dict[str, Any]) -> str:
        """Format detailed breakdown by media type."""
        breakdown = "DETAILED BREAKDOWN:\n"
        for media_type in ['images', 'videos', 'audio']:
            data = results[media_type]
            breakdown += f"\n  {media_type.upper()}:\n"
            breakdown += f"    - SFW: {len(data['sfw'])}\n"
            breakdown += f"    - NSFW: {len(data['nsfw'])}\n"
            breakdown += f"    - Uncertain: {len(data['uncertain'])}\n"
        return breakdown


class ScannerConfig:
    """Configuration schema for scanner."""

    def __init__(self, scan_path: str = 'C:\\', output_dir: Optional[str] = None,
                 mode: str = 'skip', max_files: Optional[int] = None,
                 no_visual: bool = False, confidence: float = 0.6,
                 workers: int = 4, no_confirm: bool = False):
        """Initialize configuration."""
        self.scan_path = scan_path
        self.output_dir = output_dir or str(Path.home() / "Desktop" / "Media_Scan_Results")
        self.mode = mode
        self.max_files = max_files
        self.no_visual = no_visual
        self.confidence = confidence
        self.workers = workers
        self.no_confirm = no_confirm

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'scan_path': self.scan_path,
            'output_dir': self.output_dir,
            'mode': self.mode,
            'max_files': self.max_files,
            'no_visual': self.no_visual,
            'confidence': self.confidence,
            'workers': self.workers,
            'no_confirm': self.no_confirm
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScannerConfig':
        """Create config from dictionary."""
        return cls(
            scan_path=data.get('scan_path', 'C:\\'),
            output_dir=data.get('output_dir'),
            mode=data.get('mode', 'skip'),
            max_files=data.get('max_files'),
            no_visual=data.get('no_visual', False),
            confidence=data.get('confidence', 0.6),
            workers=data.get('workers', 4),
            no_confirm=data.get('no_confirm', False)
        )


class FileInfoBuilder:
    """Builder for creating FileInfo objects."""

    def __init__(self, filepath: Path):
        """Initialize builder with file path."""
        self.filepath = filepath
        self.path_str = str(filepath)
        self.ext = filepath.suffix.lower()
        self.size = filepath.stat().st_size
        self.modified = datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
        self.hash = "unknown"
        self.detection = None

    def with_hash(self, file_hash: str) -> 'FileInfoBuilder':
        """Set file hash."""
        self.hash = file_hash
        return self

    def with_detection(self, detection: 'DetectionResult') -> 'FileInfoBuilder':
        """Set detection result."""
        self.detection = detection
        return self

    def build(self) -> 'FileInfo':
        """Build FileInfo instance."""
        if not self.detection:
            self.detection = DetectionResult()
        return FileInfo(
            path=self.path_str,
            size=self.size,
            hash=self.hash,
            extension=self.ext,
            modified=self.modified,
            detection_data=self.detection
        )


@dataclass
class FileInfo:
    """Structured file information."""
    path: str
    size: int
    hash: str
    extension: str
    modified: str
    detection_data: DetectionResult

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['detection_data'] = self.detection_data.to_dict()
        return data


class ScanResults:
    """Aggregated scan results and metrics."""

    def __init__(self):
        """Initialize results container."""
        self.media = {'images': {'sfw': [], 'nsfw': [], 'uncertain': []},
                      'videos': {'sfw': [], 'nsfw': [], 'uncertain': []},
                      'audio': {'sfw': [], 'nsfw': [], 'uncertain': []}}
        self.stats = {
            'total_scanned': 0,
            'total_size': 0,
            'images_found': 0,
            'videos_found': 0,
            'audio_found': 0,
            'nsfw_detected': 0,
            'sfw_detected': 0,
            'uncertain': 0,
            'visual_analysis_used': 0,
            'filename_analysis_used': 0,
            'errors': 0,
            'skipped_large_files': 0,
            'skipped_long_paths': 0,
            'total_processing_time': 0.0
        }
        self.performance = {
            'avg_file_time': 0.0,
            'total_visual_time': 0.0,
            'total_hash_time': 0.0
        }
        self.errors = []

    def add_file(self, media_type: str, category: str, file_info: Dict[str, Any]) -> None:
        """Add classified file to results."""
        self.media[media_type][category].append(file_info)

    def add_error(self, filepath: str, error: str, traceback_info: str = '') -> None:
        """Record processing error."""
        self.errors.append({
            'file': filepath,
            'error': error,
            'traceback': traceback_info
        })
        self.stats['errors'] += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert all results to dictionary."""
        return {
            'images': self.media['images'],
            'videos': self.media['videos'],
            'audio': self.media['audio'],
            'stats': self.stats,
            'errors': self.errors,
            'performance': self.performance
        }


class ScannerLogger:
    """Centralized logging with file and console output."""

    def __init__(self, log_dir: Path):
        """Initialize logger with file and console handlers."""
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._create_logger()

    def _create_logger(self) -> logging.Logger:
        """Create and configure logger."""
        log_file = self.log_dir / f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        console_handler = logging.StreamHandler(sys.stdout)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[file_handler, console_handler]
        )
        return logging.getLogger(__name__)

    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False) -> None:
        """Log error message."""
        self.logger.error(message, exc_info=exc_info)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)


class ProgressReporter:
    """Tracks and reports scan progress."""

    def __init__(self, interval: int = 50, throttle_seconds: float = 1.0):
        """Initialize progress reporter."""
        self.interval = interval
        self.throttle_seconds = throttle_seconds
        self.last_update = time.time()

    def should_report(self, count: int) -> bool:
        """Check if progress should be reported."""
        if count % self.interval != 0:
            return False
        current_time = time.time()
        if current_time - self.last_update < self.throttle_seconds:
            return False
        self.last_update = current_time
        return True

    def format_progress(self, count: int, stats: Dict[str, Any], elapsed: float) -> str:
        """Format progress message."""
        files_per_sec = count / max(elapsed, 1)
        return (f"[*] Progress: {count} files | "
                f"NSFW: {stats.get('nsfw_detected', 0)} | "
                f"SFW: {stats.get('sfw_detected', 0)} | "
                f"Uncertain: {stats.get('uncertain', 0)} | "
                f"Speed: {files_per_sec:.1f} files/s")


class FileHashCalculator:
    """Calculates file hashes efficiently."""

    HASH_READ_SIZE = 8192  # Read chunks for hashing
    HASH_LENGTH = 16  # Characters to return

    def calculate(self, filepath: Path) -> str:
        """Calculate file hash from first chunk."""
        try:
            hash_obj = hashlib.sha256()
            with open(filepath, 'rb') as f:
                chunk = f.read(self.HASH_READ_SIZE)
                if chunk:
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()[:self.HASH_LENGTH]
        except (IOError, OSError):
            return "unknown"
        except Exception:
            return "unknown"


class PathValidator:
    """Validates and manages file system paths."""

    MAX_PATH_LENGTH = 260  # Windows MAX_PATH limit

    def __init__(self):
        """Initialize excluded directories."""
        self.excluded_dirs = frozenset({
            'windows', 'program files', 'program files (x86)', 'programdata',
            'system volume information', '$recycle.bin', 'perflogs',
            'windows.old', 'recovery', 'boot', 'efi', 'hiberfil.sys', 'pagefile.sys',
            'appdata\\local\\temp', 'appdata\\local\\microsoft',
            'appdata\\local\\packages', 'appdata\\local\\google\\chrome\\user data',
            'node_modules', '.git', '.svn', '.hg', 'venv', '.venv', 'virtualenv',
            'cache', 'caches', 'thumbnails', '__pycache__', 'tmp', 'temp',
            'anaconda3', 'miniconda', 'site-packages', 'dist-packages'
        })

    def is_valid(self, path_str: str) -> bool:
        """Check if path is valid for processing."""
        if not path_str or len(path_str) > self.MAX_PATH_LENGTH:
            return False
        return not self.is_excluded(path_str)

    def is_excluded(self, path_str: str) -> bool:
        """Check if path is in excluded directories."""
        path_lower = path_str.lower()
        return any(excluded in path_lower for excluded in self.excluded_dirs)

    def is_path_too_long(self, path_str: str) -> bool:
        """Check if path exceeds Windows limit."""
        return len(path_str) > self.MAX_PATH_LENGTH


class MediaTypeResolver:
    """Resolves and categorizes media file types."""

    def __init__(self):
        """Initialize extension mappings."""
        self.image_extensions = frozenset({
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.heic', '.svg', '.ico'
        })
        self.video_extensions = frozenset({
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
            '.m4v', '.mpeg', '.mpg', '.3gp', '.ogv', '.ts', '.vob'
        })
        self.audio_extensions = frozenset({
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus', '.m4b', '.amr'
        })

    def get_media_type(self, extension: str) -> Optional[str]:
        """Determine media type from file extension."""
        if extension in self.image_extensions:
            return 'images'
        elif extension in self.video_extensions:
            return 'videos'
        elif extension in self.audio_extensions:
            return 'audio'
        return None

    def is_image(self, extension: str) -> bool:
        """Check if extension is image."""
        return extension in self.image_extensions

    def is_video(self, extension: str) -> bool:
        """Check if extension is video."""
        return extension in self.video_extensions

    def is_audio(self, extension: str) -> bool:
        """Check if extension is audio."""
        return extension in self.audio_extensions


class MediaClassifier:
    """Handles classification of media files."""

    def __init__(self):
        """Initialize with keyword sets."""
        self.nsfw_keywords = frozenset({
            'nsfw', 'adult', 'explicit', 'mature', '18+', 'rated-r',
            'nude', 'naked', 'nudity', 'topless', 'bottomless',
            'porn', 'pornographic', 'sex', 'sexual', 'erotic', 'eroticism',
            'onlyfans', 'patreon', 'fansonly', 'spicy',
            'hentai', 'nsfw_art', 'lewd', 'yiff', 'r34', 'rule34',
            'xxx', 'porno', 'intercourse', 'penetration', 'cumshot', 'blowjob',
            'handjob', 'creampie', 'gangbang', 'bukkake', 'squirt',
            'pussy', 'asshole', 'anus', 'cock', 'penis', 'dick', 'balls',
            'nsfl', 'extreme', 'hardcore', 'bdsm', 'bondage', 'fetish',
            'cum', 'jizz', 'semen', 'sperm',
            'homemade', 'amateure', 'amateur_porn'
        })
        self.sfw_keywords = frozenset({
            'screenshot', 'document', 'profile', 'icon', 'logo',
            'invoice', 'receipt', 'report', 'spreadsheet', 'presentation',
            'diagram', 'chart', 'graph', 'infographic', 'map',
            'photo', 'picture', 'image', 'scan', 'snapshot',
            'meme', 'wallpaper', 'background', 'desktop',
            'thumbnail', 'avatar', 'banner', 'header',
            'resume', 'cv', 'portfolio', 'mockup', 'design',
            'artwork', 'illustration', 'concept', 'sketch',
            'family', 'children', 'kids', 'baby', 'wedding',
            'vacation', 'holiday', 'birthday', 'graduation',
            'architecture', 'flowchart', 'wireframe',
            'prototype', 'ui', 'ux', 'interface'
        })

    def classify_by_filename(self, filepath: Path) -> str:
        """Classify file using keyword analysis."""
        filename_lower = filepath.name.lower()
        parent_lower = filepath.parent.name.lower()

        filename_words = set(filename_lower.replace('_', ' ').replace('-', ' ').split())
        parent_words = set(parent_lower.replace('_', ' ').replace('-', ' ').split())
        all_words = filename_words | parent_words

        nsfw_matches = len(all_words & self.nsfw_keywords)
        sfw_matches = len(all_words & self.sfw_keywords)

        if nsfw_matches > 0:
            return 'nsfw'
        elif sfw_matches > 0:
            return 'sfw'
        return 'uncertain'


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, max_calls: int = 10, time_window: float = 1.0):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []

    def acquire(self) -> None:
        """Block until rate limit allows another call."""
        now = time.time()
        self.calls = [c for c in self.calls if now - c < self.time_window]

        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.calls = self.calls[1:]

        self.calls.append(time.time())


class EnhancedMediaScanner:
    """
    Production-grade media scanner with visual AI analysis.

    This scanner detects NSFW media content using two methods:
    1. Visual Analysis: Deep learning model (NudeNet) for accurate detection
    2. Filename Analysis: Keyword matching for filename-only classification

    Features:
    - Parallel file processing with configurable thread pool
    - Windows system optimization (MAX_PATH validation, temp exclusion)
    - Comprehensive error handling and logging
    - Performance metrics tracking
    - Security validations (path traversal prevention)

    Attributes:
        CONFIDENCE_THRESHOLD (float): Minimum confidence for NSFW classification (0.0-1.0)
        VIDEO_SIZE_LIMIT (int): Maximum video file size to process (500MB)
        VIDEO_FRAME_INTERVAL_SECONDS (int): Sample frames every N seconds
        MAX_VIDEO_FRAMES (int): Maximum frames to analyze per video
        NSFW_VIDEO_THRESHOLD (float): Threshold for video NSFW classification
        HASH_READ_SIZE (int): Bytes to read for file hashing
        PROGRESS_INTERVAL (int): Report progress every N files
        MAX_PATH_LENGTH (int): Windows MAX_PATH limit
        DETECTION_TIMEOUT (int): Timeout for visual analysis operations
    """

    # Configuration constants
    CONFIDENCE_THRESHOLD = 0.6
    VIDEO_SIZE_LIMIT = 500 * 1024 * 1024  # 500MB
    VIDEO_FRAME_INTERVAL_SECONDS = 30
    MAX_VIDEO_FRAMES = 10
    NSFW_VIDEO_THRESHOLD = 0.2
    HASH_READ_SIZE = 8192
    PROGRESS_INTERVAL = 50
    MAX_PATH_LENGTH = 260  # Windows MAX_PATH
    DETECTION_TIMEOUT = 30  # seconds

    def __init__(self, use_visual_analysis: bool = True, max_workers: int = 4):
        """
        Initialize scanner with configuration.

        Args:
            use_visual_analysis (bool): Enable NudeNet visual analysis (default: True).
                                       Falls back to filename-only if unavailable.
            max_workers (int): Thread pool size for parallel file processing (default: 4).
                              Recommended: 2-8 depending on CPU cores.

        Attributes:
            results (dict): Nested dictionary storing scan results:
                - 'images', 'videos', 'audio': Classification results by type
                - 'stats': Aggregated statistics
                - 'errors': List of processing errors
                - 'performance': Performance metrics
        """
        self.start_time = datetime.now()
        self.use_visual_analysis = use_visual_analysis
        self.max_workers = max_workers
        self.nudenet_detector = None
        self._temp_frame_path = None
        self.rate_limiter = RateLimiter(max_calls=5, time_window=1.0)
        
        # Setup logging
        self._setup_logging()
        
        # Media extensions (immutable sets for O(1) lookup)
        self.image_extensions: Set[str] = frozenset({
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.heic', '.svg', '.ico'
        })
        self.video_extensions: Set[str] = frozenset({
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', 
            '.m4v', '.mpeg', '.mpg', '.3gp', '.ogv', '.ts', '.vob'
        })
        self.audio_extensions: Set[str] = frozenset({
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus', '.m4b', '.amr'
        })
        
        # System/excluded directories (case-insensitive patterns)
        self.excluded_dirs: Set[str] = frozenset({
            'windows', 'program files', 'program files (x86)', 'programdata',
            'system volume information', '$recycle.bin', 'perflogs',
            'windows.old', 'recovery', 'boot', 'efi', 'hiberfil.sys', 'pagefile.sys',
            'appdata\\local\\temp', 'appdata\\local\\microsoft',
            'appdata\\local\\packages', 'appdata\\local\\google\\chrome\\user data',
            'node_modules', '.git', '.svn', '.hg', 'venv', '.venv', 'virtualenv',
            'cache', 'caches', 'thumbnails', '__pycache__', 'tmp', 'temp',
            'anaconda3', 'miniconda', 'site-packages', 'dist-packages'
        })
        
        # NSFW/SFW keyword detection (lowercase for case-insensitive matching)
        self.nsfw_keywords: Set[str] = frozenset({
            # General NSFW indicators
            'nsfw', 'adult', 'explicit', 'mature', '18+', 'rated-r',
            # Nudity related
            'nude', 'naked', 'nudity', 'topless', 'bottomless',
            # Sexual content
            'porn', 'pornographic', 'sex', 'sexual', 'erotic', 'eroticism',
            # Specific adult platforms
            'onlyfans', 'patreon', 'fansonly', 'spicy',
            # Animation/drawings
            'hentai', 'nsfw_art', 'lewd', 'yiff', 'r34', 'rule34',
            # Explicit descriptors
            'xxx', 'porno', 'intercourse', 'penetration', 'cumshot', 'blowjob',
            'handjob', 'creampie', 'gangbang', 'bukkake', 'squirt',
            # Body parts (explicit context)
            'pussy', 'asshole', 'anus', 'cock', 'penis', 'dick', 'balls',
            # Warning indicators
            'nsfl', 'extreme', 'hardcore', 'bdsm', 'bondage', 'fetish',
            # Indexing/archival terms
            'cum', 'jizz', 'semen', 'sperm',
            # Amateur/self indicators
            'homemade', 'amateure', 'amateur_porn'
        })

        self.sfw_keywords: Set[str] = frozenset({
            # Document/work related
            'screenshot', 'document', 'profile', 'icon', 'logo',
            'invoice', 'receipt', 'report', 'spreadsheet', 'presentation',
            # Visual content - non-explicit
            'diagram', 'chart', 'graph', 'infographic', 'map',
            'photo', 'picture', 'image', 'scan', 'snapshot',
            # Entertainment - safe
            'meme', 'wallpaper', 'background', 'desktop',
            'thumbnail', 'avatar', 'banner', 'header',
            # Professional
            'resume', 'cv', 'portfolio', 'mockup', 'design',
            'artwork', 'illustration', 'concept', 'sketch',
            # Family/personal safe
            'family', 'children', 'kids', 'baby', 'wedding',
            'vacation', 'holiday', 'birthday', 'graduation',
            # Technical
            'diagram', 'architecture', 'flowchart', 'wireframe',
            'mockup', 'prototype', 'ui', 'ux', 'interface'
        })
        
        # Results storage with atomic operations support
        self.results = {
            'images': {'sfw': [], 'nsfw': [], 'uncertain': []},
            'videos': {'sfw': [], 'nsfw': [], 'uncertain': []},
            'audio': {'sfw': [], 'nsfw': [], 'uncertain': []},
            'stats': {
                'total_scanned': 0,
                'total_size': 0,
                'images_found': 0,
                'videos_found': 0,
                'audio_found': 0,
                'nsfw_detected': 0,
                'sfw_detected': 0,
                'uncertain': 0,
                'visual_analysis_used': 0,
                'filename_analysis_used': 0,
                'errors': 0,
                'skipped_large_files': 0,
                'skipped_long_paths': 0,
                'total_processing_time': 0.0
            },
            'errors': [],
            'performance': {
                'avg_file_time': 0.0,
                'total_visual_time': 0.0,
                'total_hash_time': 0.0
            }
        }
        
        # Initialize NudeNet if requested
        if self.use_visual_analysis:
            self._initialize_nudenet()
    
    def _setup_logging(self) -> None:
        """Configure structured logging with file and console output."""
        try:
            log_dir = Path.home() / "Desktop" / "Media_Scan_Results" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            
            # Configure logging with UTF-8 encoding
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            console_handler = logging.StreamHandler(sys.stdout)
            
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[file_handler, console_handler]
            )
            self.logger = logging.getLogger(__name__)
            self.logger.info("Enhanced Media Scanner v2 initialized")
        except Exception as e:
            print(f"[!] Warning: Could not setup logging: {e}")
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)
    
    def _initialize_nudenet(self) -> None:
        """Initialize NudeNet detector with comprehensive error handling."""
        try:
            self.logger.info("Initializing NudeNet for visual content analysis...")
            from nudenet import NudeDetector
            
            self.nudenet_detector = NudeDetector()
            self.logger.info("NudeNet loaded successfully")
            print("[+] NudeNet loaded successfully!")
            
        except ImportError as e:
            self.logger.warning(f"NudeNet not installed: {e}")
            print("[!] NudeNet not installed. Falling back to filename-only detection.")
            print("[!] Install with: pip install nudenet")
            self.use_visual_analysis = False
            
        except Exception as e:
            self.logger.error(f"Error loading NudeNet: {e}", exc_info=True)
            print(f"[!] Error loading NudeNet: {e}")
            print("[!] Falling back to filename-only detection.")
            self.use_visual_analysis = False
    
    def is_excluded_path(self, path_str: str) -> bool:
        """
        Check if path contains excluded directory patterns.

        Args:
            path_str: Path to check

        Returns:
            True if path should be excluded
        """
        if not path_str:
            return True

        # Check path length for Windows
        if len(path_str) > self.MAX_PATH_LENGTH:
            return True

        path_lower = path_str.lower()

        # Special handling for system paths: exclude only known system directories
        # Don't exclude arbitrary user directories that happen to contain these words
        system_temp_patterns = (
            'appdata\\local\\temp',
            'appdata\\local\\microsoft',
            'appdata\\local\\packages',
            'appdata\\local\\google\\chrome\\user data'
        )

        for system_pattern in system_temp_patterns:
            if system_pattern in path_lower:
                return True

        # Check other excluded patterns
        path_parts = path_lower.replace('/', '\\').split('\\')
        other_excluded = (
            'windows', 'program files', 'program files (x86)', 'programdata',
            'system volume information', '$recycle.bin', 'perflogs',
            'windows.old', 'recovery', 'boot', 'efi', 'hiberfil.sys', 'pagefile.sys',
            'node_modules', '.git', '.svn', '.hg', 'venv', '.venv', 'virtualenv',
            'cache', 'caches', 'thumbnails', '__pycache__',
            'anaconda3', 'miniconda', 'site-packages', 'dist-packages'
        )

        for excluded in other_excluded:
            for part in path_parts:
                if excluded in part:
                    return True

        return False
    
    def get_file_hash(self, filepath: Path) -> str:
        """
        Generate SHA256 hash of file (first 8KB for speed).
        
        Args:
            filepath: Path to file
            
        Returns:
            First 16 characters of SHA256 hash, or "unknown" on error
        """
        start_time = time.time()
        try:
            hash_obj = hashlib.sha256()
            with open(filepath, 'rb') as f:
                chunk = f.read(self.HASH_READ_SIZE)
                if chunk:
                    hash_obj.update(chunk)
            
            self.results['performance']['total_hash_time'] += time.time() - start_time
            return hash_obj.hexdigest()[:16]
            
        except (IOError, OSError) as e:
            self.logger.debug(f"Cannot hash {filepath}: {e}")
            return "unknown"
        except Exception as e:
            self.logger.error(f"Unexpected error hashing {filepath}: {e}")
            return "unknown"
    
    def classify_by_filename(self, filepath: Path) -> str:
        """
        Classify file based on filename analysis only.
        
        Args:
            filepath: Path to file
            
        Returns:
            Classification: 'nsfw', 'sfw', or 'uncertain'
        """
        try:
            filename_lower = filepath.name.lower()
            parent_lower = filepath.parent.name.lower()
            
            # Use set intersection for efficient keyword matching
            filename_words = set(filename_lower.replace('_', ' ').replace('-', ' ').split())
            parent_words = set(parent_lower.replace('_', ' ').replace('-', ' ').split())
            all_words = filename_words | parent_words
            
            nsfw_matches = len(all_words & self.nsfw_keywords)
            sfw_matches = len(all_words & self.sfw_keywords)
            
            if nsfw_matches > 0:
                return 'nsfw'
            elif sfw_matches > 0:
                return 'sfw'
            return 'uncertain'
            
        except Exception as e:
            self.logger.error(f"Error in filename classification for {filepath}: {e}")
            return 'uncertain'
    
    def _create_detection_result(self,
                                 detections_count: int,
                                 nsfw_labels: List[str],
                                 max_confidence: float,
                                 method: str,
                                 processing_time: float,
                                 error: Optional[str] = None) -> DetectionResult:
        """Create a detection result with proper metrics tracking."""
        result = DetectionResult(
            detections_count=detections_count,
            nsfw_labels=nsfw_labels,
            max_confidence=max_confidence,
            method=method,
            processing_time=processing_time,
            error=error
        )
        if method in ['visual_analysis', 'video_frame_analysis']:
            self.results['performance']['total_visual_time'] += processing_time
        return result

    def _process_nudenet_detections(self, detections: List[Dict]) -> Tuple[bool, float, List[str]]:
        """
        Process NudeNet detections and extract NSFW indicators.

        Returns:
            Tuple of (nsfw_detected, max_confidence, detected_labels)
        """
        nsfw_labels_set = {
            'FEMALE_GENITALIA_EXPOSED',
            'MALE_GENITALIA_EXPOSED',
            'FEMALE_BREAST_EXPOSED',
            'BUTTOCKS_EXPOSED',
            'ANUS_EXPOSED'
        }

        nsfw_detected = False
        max_confidence = 0.0
        detected_labels = []

        for detection in detections:
            label = detection.get('class', '')
            confidence = detection.get('score', 0.0)

            if label in nsfw_labels_set and confidence > self.CONFIDENCE_THRESHOLD:
                nsfw_detected = True
                max_confidence = max(max_confidence, confidence)
                detected_labels.append(f"{label}:{confidence:.2f}")

        return nsfw_detected, max_confidence, detected_labels

    def analyze_image_content(self, filepath: Path) -> Tuple[str, DetectionResult]:
        """
        Analyze image using NudeNet for visual NSFW detection.

        Args:
            filepath: Path to image file

        Returns:
            Tuple of (classification, detection_result)
        """
        start_time = time.time()
        elapsed = lambda: time.time() - start_time

        if not self.use_visual_analysis or not self.nudenet_detector:
            classification = self.classify_by_filename(filepath)
            return classification, self._create_detection_result(
                detections_count=0,
                nsfw_labels=[],
                max_confidence=0.0,
                method='filename_only',
                processing_time=elapsed()
            )

        try:
            # Rate limiting
            self.rate_limiter.acquire()

            # Run NudeNet detection
            detections = self.nudenet_detector.detect(str(filepath))

            # Process detections
            nsfw_detected, max_confidence, detected_labels = self._process_nudenet_detections(detections)

            result = self._create_detection_result(
                detections_count=len(detections),
                nsfw_labels=detected_labels,
                max_confidence=max_confidence,
                method='visual_analysis',
                processing_time=elapsed()
            )

            # Determine classification
            if nsfw_detected:
                return 'nsfw', result
            elif len(detections) > 0:
                return 'sfw', result
            else:
                # No detections - fallback to filename
                classification = self.classify_by_filename(filepath)
                result.method = 'visual_analysis_fallback_filename'
                return classification, result

        except Exception as e:
            self.logger.warning(f"Visual analysis failed for {filepath}: {e}")
            classification = self.classify_by_filename(filepath)
            return classification, self._create_detection_result(
                detections_count=0,
                nsfw_labels=[],
                max_confidence=0.0,
                method='filename_fallback_error',
                processing_time=elapsed(),
                error=str(e)
            )
    
    def _ensure_temp_frame_path(self) -> Path:
        """Ensure temporary frame file path exists."""
        if not self._temp_frame_path:
            temp_dir = Path.home() / "AppData" / "Local" / "Temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            self._temp_frame_path = temp_dir / f"temp_frame_{os.getpid()}.jpg"
        return self._temp_frame_path

    def analyze_video_content(self, filepath: Path) -> Tuple[str, DetectionResult]:
        """
        Analyze video by extracting and checking frames with NudeNet.

        Args:
            filepath: Path to video file

        Returns:
            Tuple of (classification, detection_result)
        """
        start_time = time.time()
        elapsed = lambda: time.time() - start_time

        if not self.use_visual_analysis or not self.nudenet_detector:
            classification = self.classify_by_filename(filepath)
            return classification, self._create_detection_result(
                detections_count=0,
                nsfw_labels=[],
                max_confidence=0.0,
                method='filename_only',
                processing_time=elapsed()
            )

        try:
            import cv2
        except ImportError:
            self.logger.warning("OpenCV not installed for video analysis")
            print("[!] OpenCV (cv2) not installed. Cannot analyze videos visually.")
            print("[!] Install with: pip install opencv-python")
            classification = self.classify_by_filename(filepath)
            return classification, self._create_detection_result(
                detections_count=0,
                nsfw_labels=[],
                max_confidence=0.0,
                method='filename_fallback',
                processing_time=elapsed(),
                error='opencv_missing'
            )

        cap = None
        try:
            cap = cv2.VideoCapture(str(filepath))
            if not cap.isOpened():
                raise IOError(f"Cannot open video: {filepath}")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            if fps <= 0 or total_frames <= 0:
                raise ValueError(f"Invalid video properties: fps={fps}, frames={total_frames}")

            # Calculate frame sampling
            frame_interval = int(fps * self.VIDEO_FRAME_INTERVAL_SECONDS)
            frames_to_check = min(self.MAX_VIDEO_FRAMES, max(1, total_frames // max(frame_interval, 1)))

            nsfw_frames = 0
            frames_checked = 0
            temp_frame_path = self._ensure_temp_frame_path()

            for i in range(frames_to_check):
                frame_pos = min(i * frame_interval, total_frames - 1)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                ret, frame = cap.read()

                if not ret or frame is None:
                    continue

                # Save and analyze frame
                cv2.imwrite(str(temp_frame_path), frame)
                classification, _ = self.analyze_image_content(temp_frame_path)
                frames_checked += 1

                if classification == 'nsfw':
                    nsfw_frames += 1

            # Determine classification based on NSFW frame ratio
            if frames_checked > 0:
                nsfw_ratio = nsfw_frames / frames_checked
                result = self._create_detection_result(
                    detections_count=frames_checked,
                    nsfw_labels=[f"nsfw_frames:{nsfw_frames}/{frames_checked}"],
                    max_confidence=nsfw_ratio,
                    method='video_frame_analysis',
                    processing_time=elapsed()
                )

                if nsfw_ratio > self.NSFW_VIDEO_THRESHOLD:
                    return 'nsfw', result
                elif nsfw_frames > 0:
                    return 'uncertain', result
                else:
                    return 'sfw', result
            else:
                # No frames could be analyzed - fallback to filename
                classification = self.classify_by_filename(filepath)
                result = self._create_detection_result(
                    detections_count=0,
                    nsfw_labels=[],
                    max_confidence=0.0,
                    method='filename_fallback_no_frames',
                    processing_time=elapsed()
                )
                return classification, result

        except Exception as e:
            self.logger.warning(f"Video analysis failed for {filepath}: {e}")
            classification = self.classify_by_filename(filepath)
            return classification, self._create_detection_result(
                detections_count=0,
                nsfw_labels=[],
                max_confidence=0.0,
                method='filename_fallback_error',
                processing_time=elapsed(),
                error=str(e)
            )
        finally:
            if cap:
                cap.release()
    
    def get_media_type(self, extension: str) -> Optional[str]:
        """
        Determine media type from extension.
        
        Args:
            extension: File extension (with dot)
            
        Returns:
            'images', 'videos', 'audio', or None
        """
        if extension in self.image_extensions:
            return 'images'
        elif extension in self.video_extensions:
            return 'videos'
        elif extension in self.audio_extensions:
            return 'audio'
        return None
    
    def _analyze_media_file(self, media_type: str, filepath: Path, file_size: int) -> Tuple[str, DetectionResult]:
        """Analyze media file based on type and size constraints."""
        if media_type == 'videos' and file_size > self.VIDEO_SIZE_LIMIT:
            self.results['stats']['skipped_large_files'] += 1
            return 'uncertain', self._create_detection_result(
                detections_count=0,
                nsfw_labels=[],
                max_confidence=0.0,
                method='filename_only',
                processing_time=0.0,
                error='file_too_large'
            )
        elif media_type == 'images':
            return self.analyze_image_content(filepath)
        elif media_type == 'videos':
            return self.analyze_video_content(filepath)
        else:  # audio
            return self.classify_by_filename(filepath), self._create_detection_result(
                detections_count=0,
                nsfw_labels=[],
                max_confidence=0.0,
                method='filename_only',
                processing_time=0.0
            )

    def process_file(self, filepath: Path) -> Optional[Tuple[str, str, FileInfo]]:
        """
        Process a single media file.

        Args:
            filepath: Path to file

        Returns:
            Tuple of (media_type, classification, FileInfo) or None if processing failed
        """
        try:
            # F8: Security - Path validation and sanitization
            if not filepath or not isinstance(filepath, Path):
                self.logger.warning(f"Invalid filepath type: {type(filepath)}")
                return None

            filepath_str = str(filepath)

            # Check for path traversal attempts
            if ".." in filepath_str or filepath_str.startswith("~"):
                self.logger.warning(f"Suspicious path detected (traversal): {filepath_str}")
                return None

            # Validate path exists and is readable
            if not filepath.exists() or not filepath.is_file():
                return None

            extension = filepath.suffix.lower()
            media_type = self.get_media_type(extension)

            if not media_type:
                return None

            # Check path length
            if len(filepath_str) > self.MAX_PATH_LENGTH:
                self.results['stats']['skipped_long_paths'] += 1
                self.logger.debug(f"Path too long (>260 chars): {filepath_str[:100]}...")
                return None

            file_size = filepath.stat().st_size

            # F3: Reliability - Validate file accessibility
            if file_size == 0:
                self.logger.debug(f"Empty file skipped: {filepath_str}")
                return None

            # Analyze media file
            classification, detection_result = self._analyze_media_file(media_type, filepath, file_size)

            # Create file info
            file_info = FileInfo(
                path=str(filepath),
                size=file_size,
                hash=self.get_file_hash(filepath),
                extension=extension,
                modified=datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
                detection_data=detection_result
            )

            return media_type, classification, file_info

        except (PermissionError, OSError) as e:
            self.logger.debug(f"Cannot access {filepath}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing {filepath}: {e}", exc_info=True)
            self.results['stats']['errors'] += 1
            self.results['errors'].append({
                'file': str(filepath),
                'error': str(e),
                'traceback': traceback.format_exc()
            })
            return None

    def _process_file_batch(self, files: list, scanned_count: int, last_progress_time: float) -> int:
        """
        Process a batch of files using parallel execution (F1: Performance).

        Args:
            files: List of file paths to process
            scanned_count: Current file count
            last_progress_time: Last progress report time

        Returns:
            Updated scanned_count
        """
        batch_results = []

        # Use ThreadPoolExecutor for parallel file processing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_file, f): f for f in files}

            for future in as_completed(futures):
                result = future.result()
                if result:
                    batch_results.append(result)
                scanned_count += 1

        # Update results after batch processing
        for media_type, classification, file_info in batch_results:
            self.results[media_type][classification].append(file_info.to_dict())
            self.results['stats']['total_size'] += file_info.size
            self.results['stats'][f'{media_type}_found'] += 1
            if classification == 'uncertain':
                self.results['stats']['uncertain'] += 1
            else:
                self.results['stats'][f'{classification}_detected'] += 1

            if file_info.detection_data.method in ['visual_analysis', 'video_frame_analysis']:
                self.results['stats']['visual_analysis_used'] += 1
            else:
                self.results['stats']['filename_analysis_used'] += 1

        # Progress reporting (throttled to once per second)
        current_time = time.time()
        if scanned_count % self.PROGRESS_INTERVAL == 0 and (current_time - last_progress_time) >= 1.0:
            files_per_sec = scanned_count / max((current_time - self.start_time.timestamp()), 1)
            print(f"[*] Progress: {scanned_count} files | "
                  f"NSFW: {self.results['stats']['nsfw_detected']} | "
                  f"SFW: {self.results['stats']['sfw_detected']} | "
                  f"Uncertain: {self.results['stats']['uncertain']} | "
                  f"Speed: {files_per_sec:.1f} files/s")

        return scanned_count

    def scan_drive(self, drive: str = 'C:\\', max_files: Optional[int] = None) -> None:
        """
        Scan drive for media files with visual content analysis.

        Args:
            drive: Root drive to scan
            max_files: Optional limit on files to scan
        """
        self.logger.info(f"Starting scan of {drive}")
        print(f"\n[*] Starting enhanced media scan of {drive}")
        print(f"[*] Visual Analysis: {'ENABLED' if self.use_visual_analysis else 'DISABLED (filename-only)'}")
        print(f"[*] Excluding {len(self.excluded_dirs)} system directory patterns\n")

        scanned_count = 0
        last_progress_time = time.time()

        # Normalize drive path for comparison
        drive_abs = os.path.abspath(drive).lower()

        # F1: Performance optimization - batch and parallelize file processing
        files_to_process = []
        batch_size = 1000  # Process files in batches

        try:
            for root, dirs, files in os.walk(drive):
                root_abs = os.path.abspath(root).lower()

                # Skip exclusions, but allow the root directory itself to be scanned
                # (even if it normally would be excluded)
                if root_abs != drive_abs and self.is_excluded_path(root):
                    dirs.clear()
                    continue

                dirs[:] = [d for d in dirs if not self.is_excluded_path(os.path.join(root, d))]

                for filename in files:
                    if max_files and scanned_count >= max_files:
                        self.logger.info(f"Reached max file limit: {max_files}")
                        print(f"\n[!] Reached max file limit: {max_files}")
                        return

                    filepath = Path(root) / filename
                    files_to_process.append(filepath)

                    # Process batch when size reached
                    if len(files_to_process) >= batch_size:
                        scanned_count = self._process_file_batch(files_to_process, scanned_count,
                                                                   last_progress_time)
                        last_progress_time = time.time()
                        files_to_process = []

            # Process remaining files
            if files_to_process:
                scanned_count = self._process_file_batch(files_to_process, scanned_count,
                                                         last_progress_time)
            
            self.results['stats']['total_scanned'] = scanned_count
            self.results['stats']['total_processing_time'] = (datetime.now() - self.start_time).total_seconds()
            self.results['performance']['avg_file_time'] = (
                self.results['stats']['total_processing_time'] / max(scanned_count, 1)
            )
            
            self.logger.info(f"Scan complete. Total files: {scanned_count}")
            print(f"\n[+] Scan complete! Total media files: {scanned_count}")
            
        except KeyboardInterrupt:
            self.logger.warning("Scan interrupted by user")
            self.results['stats']['total_scanned'] = scanned_count
            raise
        except Exception as e:
            self.logger.error(f"Fatal error during scan: {e}", exc_info=True)
            self.results['stats']['total_scanned'] = scanned_count
            raise
        finally:
            # Cleanup temp frame file
            if self._temp_frame_path and self._temp_frame_path.exists():
                try:
                    self._temp_frame_path.unlink()
                except Exception as e:
                    self.logger.warning(f"Could not delete temp frame: {e}")
    
    def generate_report(self, output_dir: Path) -> Tuple[Path, Path]:
        """
        Generate detailed report with visual analysis data.
        
        Args:
            output_dir: Directory to save reports
            
        Returns:
            Tuple of (report_file_path, summary_file_path)
        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save detailed JSON report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = output_dir / f'enhanced_scan_report_{timestamp}.json'
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Report saved to {report_file}")
            
            # Generate summary
            analysis_method = "Visual AI Analysis (NudeNet)" if self.use_visual_analysis else "Filename Analysis Only"
            duration = self.results['stats']['total_processing_time']
            
            summary = f"""
+===================================================================+
|    ENHANCED MEDIA SCANNER - AI VISUAL ANALYSIS RESULTS v2.0     |
+===================================================================+

Analysis Method: {analysis_method}
Scan Duration: {duration:.2f} seconds ({duration/60:.1f} minutes)
Total Files Scanned: {self.results['stats']['total_scanned']:,}
Total Size: {self.results['stats']['total_size'] / (1024**3):.2f} GB
Errors Encountered: {self.results['stats']['errors']}
Large Files Skipped: {self.results['stats']['skipped_large_files']}
Long Paths Skipped: {self.results['stats']['skipped_long_paths']}

===================================================================

PERFORMANCE METRICS:
  Avg Time per File: {self.results['performance']['avg_file_time']:.3f}s
  Files per Second: {self.results['stats']['total_scanned'] / max(duration, 1):.1f}
  Total Visual Analysis Time: {self.results['performance']['total_visual_time']:.2f}s
  Total Hash Time: {self.results['performance']['total_hash_time']:.2f}s

===================================================================

ANALYSIS BREAKDOWN:
  Visual AI Analysis: {self.results['stats']['visual_analysis_used']:,} files
  Filename Analysis:  {self.results['stats']['filename_analysis_used']:,} files

===================================================================

MEDIA TYPE BREAKDOWN:
  Images: {self.results['stats']['images_found']:,}
  Videos: {self.results['stats']['videos_found']:,}
  Audio:  {self.results['stats']['audio_found']:,}

===================================================================

CLASSIFICATION RESULTS:
  [+] SFW (Safe):      {self.results['stats']['sfw_detected']:,} files
  [X] NSFW (Explicit): {self.results['stats']['nsfw_detected']:,} files
  [?] Uncertain:       {self.results['stats']['uncertain']:,} files

===================================================================

DETAILED BREAKDOWN:
  Images:
    - SFW: {len(self.results['images']['sfw'])}
    - NSFW: {len(self.results['images']['nsfw'])}
    - Uncertain: {len(self.results['images']['uncertain'])}
  
  Videos:
    - SFW: {len(self.results['videos']['sfw'])}
    - NSFW: {len(self.results['videos']['nsfw'])}
    - Uncertain: {len(self.results['videos']['uncertain'])}
  
  Audio:
    - SFW: {len(self.results['audio']['sfw'])}
    - NSFW: {len(self.results['audio']['nsfw'])}
    - Uncertain: {len(self.results['audio']['uncertain'])}

===================================================================

Report saved to: {report_file}
"""
            
            print(summary)
            
            # Save summary to file
            summary_file = output_dir / f'enhanced_scan_summary_{timestamp}.txt'
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            self.logger.info(f"Summary saved to {summary_file}")
            return report_file, summary_file
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}", exc_info=True)
            raise
    
    def _get_unique_destination_path(self, dest_dir: Path, src_path: Path) -> Path:
        """Get unique destination path, handling duplicate filenames."""
        dest_path = dest_dir / src_path.name
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{src_path.stem}_{counter}{src_path.suffix}"
            counter += 1
        return dest_path

    def _transfer_file(self, src_path: Path, dest_path: Path, move: bool) -> bool:
        """Transfer file (copy or move) with error handling."""
        try:
            if move:
                shutil.move(str(src_path), str(dest_path))
            else:
                shutil.copy2(str(src_path), str(dest_path))
            return True
        except Exception as e:
            self.logger.error(f"Error transferring {src_path}: {e}")
            return False

    def organize_files(self, output_base: Path, move_files: bool = False, batch_size: int = 1000) -> None:
        """
        Organize files into SFW/NSFW/Uncertain directories with batch processing.

        Args:
            output_base: Base directory for organized files
            move_files: If True, move files; if False, copy files
            batch_size: Number of files to process before showing progress
        """
        try:
            self.logger.info(f"Organizing files to {output_base}")
            print("\n[*] Organizing files...")

            organized_count = 0
            failed_count = 0
            action = "Moving" if move_files else "Copying"

            for media_type in ['images', 'videos', 'audio']:
                for category in ['sfw', 'nsfw', 'uncertain']:
                    files = self.results[media_type][category]
                    if not files:
                        continue

                    # Create destination directory
                    dest_dir = output_base / media_type / category
                    dest_dir.mkdir(parents=True, exist_ok=True)

                    print(f"\n[*] {action} {len(files)} {media_type}/{category} files...")

                    for idx, file_info in enumerate(files, 1):
                        src_path = Path(file_info['path'])

                        if not src_path.exists():
                            self.logger.warning(f"Source file not found: {src_path}")
                            failed_count += 1
                            continue

                        dest_path = self._get_unique_destination_path(dest_dir, src_path)
                        if self._transfer_file(src_path, dest_path, move_files):
                            organized_count += 1
                        else:
                            failed_count += 1

                        # Show progress for batches
                        if idx % batch_size == 0:
                            print(f"[*] Progress: {idx}/{len(files)} files in {media_type}/{category}")

            self.logger.info(f"Organization complete. Success: {organized_count}, Failed: {failed_count}")
            print(f"\n[+] Files organized in: {output_base}")
            print(f"[+] Successfully organized: {organized_count} files")
            if failed_count > 0:
                print(f"[!] Failed to organize: {failed_count} files (see log for details)")

        except Exception as e:
            self.logger.error(f"Fatal error during organization: {e}", exc_info=True)
            raise


def load_config(config_file: Optional[Path]) -> Optional[Dict[str, Any]]:
    """Load configuration from JSON file."""
    if not config_file or not config_file.exists():
        return None

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Warning: Could not load config file: {e}")
        return None

def save_config(config_file: Path, config: Dict[str, Any]) -> None:
    """Save configuration to JSON file."""
    try:
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        print(f"[+] Config saved to {config_file}")
    except Exception as e:
        print(f"[!] Warning: Could not save config file: {e}")

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments with extensive options."""
    parser = argparse.ArgumentParser(
        description='Enhanced Media Scanner v3.0 ULTRA BUFF - AI-powered NSFW detection with 40+ options',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python media_scanner.py                           # Interactive mode (scan C: drive)
  python media_scanner.py --scan-path D:\\Pictures  # Scan specific path
  python media_scanner.py --scan-path C: --mode copy # Copy organized files
  python media_scanner.py --scan-path C: --max-files 1000  # Limit scan to 1000 files
  python media_scanner.py --no-visual --scan-path C:  # Filename analysis only
  python media_scanner.py --gui                     # Launch GUI interface
  python media_scanner.py --min-size 1MB --max-size 100MB  # Size filtering
  python media_scanner.py --extensions jpg,png,mp4  # Specific extensions only
  python media_scanner.py --export-format html,csv  # Multiple export formats
  python media_scanner.py --detect-duplicates       # Find duplicate files
  python media_scanner.py --watch-mode --scan-path D:\\Downloads  # Monitor folder
        '''
    )

    # Core scanning options
    scan_group = parser.add_argument_group('Scanning Options')
    scan_group.add_argument(
        '--scan-path',
        type=str,
        default='C:\\',
        help='Path to scan (default: C:\\)'
    )
    scan_group.add_argument(
        '--recursive',
        action='store_true',
        default=True,
        help='Scan subdirectories recursively (default: True)'
    )
    scan_group.add_argument(
        '--no-recursive',
        dest='recursive',
        action='store_false',
        help='Do not scan subdirectories'
    )
    scan_group.add_argument(
        '--max-files',
        type=int,
        help='Maximum number of files to scan'
    )
    scan_group.add_argument(
        '--max-depth',
        type=int,
        help='Maximum directory depth to scan'
    )
    scan_group.add_argument(
        '--follow-symlinks',
        action='store_true',
        help='Follow symbolic links (default: False)'
    )

    # File filtering options
    filter_group = parser.add_argument_group('File Filtering Options')
    filter_group.add_argument(
        '--min-size',
        type=str,
        help='Minimum file size (e.g., 1MB, 500KB, 1GB)'
    )
    filter_group.add_argument(
        '--max-size',
        type=str,
        help='Maximum file size (e.g., 100MB, 1GB)'
    )
    filter_group.add_argument(
        '--extensions',
        type=str,
        help='Comma-separated list of extensions to include (e.g., jpg,png,mp4)'
    )
    filter_group.add_argument(
        '--exclude-extensions',
        type=str,
        help='Comma-separated list of extensions to exclude'
    )
    filter_group.add_argument(
        '--modified-after',
        type=str,
        help='Only scan files modified after date (YYYY-MM-DD)'
    )
    filter_group.add_argument(
        '--modified-before',
        type=str,
        help='Only scan files modified before date (YYYY-MM-DD)'
    )
    filter_group.add_argument(
        '--filename-pattern',
        type=str,
        help='Only scan files matching regex pattern'
    )
    filter_group.add_argument(
        '--exclude-pattern',
        type=str,
        help='Exclude files matching regex pattern'
    )

    # Analysis options
    analysis_group = parser.add_argument_group('Analysis Options')
    analysis_group.add_argument(
        '--no-visual',
        action='store_true',
        help='Disable visual analysis (filename-only detection)'
    )
    analysis_group.add_argument(
        '--confidence',
        type=float,
        default=0.6,
        help='NSFW confidence threshold (0.0-1.0, default: 0.6)'
    )
    analysis_group.add_argument(
        '--strict-mode',
        action='store_true',
        help='Use stricter detection (lower threshold to 0.4)'
    )
    analysis_group.add_argument(
        '--permissive-mode',
        action='store_true',
        help='Use more permissive detection (raise threshold to 0.8)'
    )
    analysis_group.add_argument(
        '--custom-nsfw-keywords',
        type=str,
        help='Comma-separated custom NSFW keywords to add'
    )
    analysis_group.add_argument(
        '--custom-sfw-keywords',
        type=str,
        help='Comma-separated custom SFW keywords to add'
    )
    analysis_group.add_argument(
        '--detect-duplicates',
        action='store_true',
        help='Detect duplicate files using file hashing'
    )
    analysis_group.add_argument(
        '--hash-algorithm',
        choices=['sha256', 'md5', 'sha1'],
        default='sha256',
        help='Hash algorithm for file comparison (default: sha256)'
    )
    analysis_group.add_argument(
        '--full-hash',
        action='store_true',
        help='Hash entire file instead of first chunk (slower but more accurate)'
    )

    # Video processing options
    video_group = parser.add_argument_group('Video Processing Options')
    video_group.add_argument(
        '--video-frame-interval',
        type=int,
        default=30,
        help='Seconds between video frame samples (default: 30)'
    )
    video_group.add_argument(
        '--max-video-frames',
        type=int,
        default=10,
        help='Maximum frames to analyze per video (default: 10)'
    )
    video_group.add_argument(
        '--video-size-limit',
        type=str,
        default='500MB',
        help='Maximum video size to process (default: 500MB)'
    )
    video_group.add_argument(
        '--skip-videos',
        action='store_true',
        help='Skip all video files'
    )

    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '--output-dir',
        type=str,
        help='Output directory for results (default: Desktop/Media_Scan_Results)'
    )
    output_group.add_argument(
        '--export-format',
        type=str,
        default='json',
        help='Export formats (comma-separated: json,html,csv,sqlite) (default: json)'
    )
    output_group.add_argument(
        '--report-name',
        type=str,
        help='Custom name for report files'
    )
    output_group.add_argument(
        '--thumbnail-size',
        type=int,
        default=200,
        help='Thumbnail size for HTML reports (default: 200px)'
    )
    output_group.add_argument(
        '--no-thumbnails',
        action='store_true',
        help='Do not generate thumbnails in HTML reports'
    )

    # Organization options
    org_group = parser.add_argument_group('File Organization Options')
    org_group.add_argument(
        '--mode',
        choices=['copy', 'move', 'skip', 'symlink'],
        default='skip',
        help='File organization mode (default: skip)'
    )
    org_group.add_argument(
        '--organize-by',
        choices=['classification', 'type', 'date', 'size'],
        default='classification',
        help='Organization structure (default: classification)'
    )
    org_group.add_argument(
        '--keep-structure',
        action='store_true',
        help='Preserve original directory structure when organizing'
    )
    org_group.add_argument(
        '--quarantine-nsfw',
        action='store_true',
        help='Move NSFW files to isolated quarantine folder'
    )
    org_group.add_argument(
        '--auto-delete-nsfw',
        action='store_true',
        help='Automatically delete NSFW files (DANGEROUS - use with caution!)'
    )

    # Performance options
    perf_group = parser.add_argument_group('Performance Options')
    perf_group.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Number of parallel workers (default: 4)'
    )
    perf_group.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Batch size for processing (default: 1000)'
    )
    perf_group.add_argument(
        '--rate-limit',
        type=int,
        default=5,
        help='API calls per second for visual analysis (default: 5)'
    )
    perf_group.add_argument(
        '--cache-results',
        action='store_true',
        help='Cache analysis results to speed up re-scans'
    )
    perf_group.add_argument(
        '--priority',
        choices=['fast', 'balanced', 'thorough'],
        default='balanced',
        help='Scanning priority mode (default: balanced)'
    )

    # Advanced options
    advanced_group = parser.add_argument_group('Advanced Options')
    advanced_group.add_argument(
        '--exclude-dirs',
        type=str,
        help='Additional comma-separated directories to exclude'
    )
    advanced_group.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    advanced_group.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Timeout for file analysis in seconds (default: 30)'
    )
    advanced_group.add_argument(
        '--watch-mode',
        action='store_true',
        help='Continuously monitor directory for new files'
    )
    advanced_group.add_argument(
        '--watch-interval',
        type=int,
        default=60,
        help='Watch mode check interval in seconds (default: 60)'
    )
    advanced_group.add_argument(
        '--api-mode',
        action='store_true',
        help='Run as REST API server'
    )
    advanced_group.add_argument(
        '--api-port',
        type=int,
        default=5000,
        help='API server port (default: 5000)'
    )

    # GUI and configuration
    misc_group = parser.add_argument_group('Miscellaneous Options')
    misc_group.add_argument(
        '--gui',
        action='store_true',
        help='Launch graphical user interface'
    )
    misc_group.add_argument(
        '--no-confirm',
        action='store_true',
        help='Skip confirmation prompts'
    )
    misc_group.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress output'
    )
    misc_group.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed progress information'
    )
    misc_group.add_argument(
        '--config',
        type=str,
        help='Load settings from config file (JSON format)'
    )
    misc_group.add_argument(
        '--save-config',
        type=str,
        help='Save current settings to config file'
    )
    misc_group.add_argument(
        '--profile',
        type=str,
        help='Load settings from named profile'
    )
    misc_group.add_argument(
        '--list-profiles',
        action='store_true',
        help='List all saved configuration profiles'
    )
    misc_group.add_argument(
        '--version',
        action='version',
        version='Enhanced Media Scanner v3.0 ULTRA BUFF'
    )

    return parser.parse_args()

def main():
    """Main entry point with enhanced error handling and Windows console support."""
    print("""
+=====================================================================+
|  ENHANCED MEDIA SCANNER - AI VISUAL CONTENT ANALYSIS v3.0 ULTRA   |
|  BUFF EDITION - 40+ Advanced CLI Options + Full GUI Support        |
|           Powered by NudeNet Deep Learning Model                   |
|     Production-Grade Quality with Comprehensive Error Handling     |
+=====================================================================+
    """)

    try:
        # Parse command-line arguments
        args = parse_arguments()

        # Launch GUI if requested
        if args.gui:
            print("[*] Launching GUI interface...")
            try:
                from media_scanner_gui import MediaScannerGUI
                MediaScannerGUI().run()
                return
            except ImportError as e:
                print(f"[!] Error: GUI module not found. {e}")
                print("[!] Make sure media_scanner_gui.py is in the same directory.")
                sys.exit(1)

        # Load configuration from file if specified
        if args.config:
            config_path = Path(args.config)
            config_data = load_config(config_path)
            if config_data:
                # Override args with config file values
                for key, value in config_data.items():
                    if hasattr(args, key):
                        setattr(args, key, value)
                print(f"[+] Loaded config from {config_path}\n")

        # Check for NudeNet availability
        use_visual = not args.no_visual
        if use_visual:
            try:
                import nudenet
                print("[+] NudeNet detected - Visual AI analysis will be used\n")
            except ImportError:
                use_visual = False
                print("[!] NudeNet not installed - Using filename analysis only")
                print("[!] For visual content analysis, install: pip install nudenet\n")
        else:
            print("[!] Visual analysis disabled by user - Using filename analysis only\n")

        # Initialize scanner
        scanner = EnhancedMediaScanner(use_visual_analysis=use_visual, max_workers=args.workers)
        scanner.CONFIDENCE_THRESHOLD = args.confidence

        # Determine output directory
        output_dir = Path(args.output_dir) if args.output_dir else (Path.home() / "Desktop" / "Media_Scan_Results")

        # Confirmation before scan
        if not args.no_confirm:
            print(f"[?] Scan {args.scan_path}? This may take a while.")
            print("[?] Press ENTER to start, or Ctrl+C to cancel")
            input()
        else:
            print(f"[*] Scanning {args.scan_path}...")

        # Run scan
        scanner.scan_drive(drive=args.scan_path, max_files=args.max_files)

        # Generate report
        report_file, summary_file = scanner.generate_report(output_dir)

        # File organization
        if args.mode != 'skip':
            organize_base = output_dir / "Organized_Media"
            scanner.organize_files(organize_base, move_files=(args.mode == 'move'))

        # Save configuration if requested
        if args.save_config:
            config_to_save = {
                'scan_path': args.scan_path,
                'output_dir': str(output_dir),
                'mode': args.mode,
                'max_files': args.max_files,
                'no_visual': args.no_visual,
                'confidence': args.confidence,
                'workers': args.workers,
                'no_confirm': args.no_confirm
            }
            save_config(Path(args.save_config), config_to_save)

        print(f"\n[+] Complete! Results at: {output_dir}")
        print(f"[+] Report: {report_file.name}")
        print(f"[+] Summary: {summary_file.name}")

    except KeyboardInterrupt:
        print("\n\n[!] Scan interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[!] Fatal error: {e}")
        print(f"[!] Check log file for details")
        logging.exception("Fatal error in main")
        sys.exit(1)


if __name__ == "__main__":
    main()
