#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Features Module for Enhanced Media Scanner v3.0
Provides advanced AI-powered media analysis capabilities

Features:
- Object Detection & Tagging (YOLO/CLIP)
- Color Analysis & Dominant Colors
- Face Detection & Recognition
- Scene Classification
- Quality & Resolution Metrics
- Video Scene Detection
- Audio Transcription & Analysis
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from PIL import Image
from collections import Counter
import hashlib

logger = logging.getLogger(__name__)


class ObjectDetector:
    """Detects objects in images using YOLO/CLIP for auto-tagging."""

    def __init__(self):
        self.model = None
        self.available = False
        self._initialize()

    def _initialize(self):
        """Initialize object detection model."""
        try:
            # Try YOLOv8 first (faster, good for common objects)
            from ultralytics import YOLO
            self.model = YOLO('yolov8n.pt')  # Nano model for speed
            self.available = True
            self.model_type = 'yolo'
            logger.info("YOLOv8 object detection initialized")
        except ImportError:
            try:
                # Fallback to CLIP (better for semantic understanding)
                import clip
                import torch
                self.model, self.preprocess = clip.load("ViT-B/32", device="cpu")
                self.available = True
                self.model_type = 'clip'
                logger.info("CLIP object detection initialized")
            except ImportError:
                logger.warning("No object detection model available (install ultralytics or clip)")
                self.available = False

    def detect_objects(self, image_path: str, confidence: float = 0.5) -> List[Dict[str, Any]]:
        """
        Detect objects in image and return tags.

        Returns:
            List of detected objects with format:
            [{'name': 'car', 'confidence': 0.85, 'bbox': [x1, y1, x2, y2]}, ...]
        """
        if not self.available:
            return []

        try:
            if self.model_type == 'yolo':
                return self._detect_yolo(image_path, confidence)
            elif self.model_type == 'clip':
                return self._detect_clip(image_path, confidence)
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return []

    def _detect_yolo(self, image_path: str, confidence: float) -> List[Dict[str, Any]]:
        """Detect objects using YOLO."""
        results = self.model(image_path, conf=confidence, verbose=False)

        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                class_name = result.names[cls_id]
                conf = float(box.conf[0])
                bbox = box.xyxy[0].tolist()

                detections.append({
                    'name': class_name,
                    'confidence': conf,
                    'bbox': bbox
                })

        return detections

    def _detect_clip(self, image_path: str, confidence: float) -> List[Dict[str, Any]]:
        """Detect objects using CLIP zero-shot classification."""
        import torch
        from PIL import Image

        # Common object categories for classification
        categories = [
            "person", "car", "dog", "cat", "building", "tree", "flower",
            "food", "animal", "vehicle", "furniture", "electronics",
            "nature", "indoor scene", "outdoor scene", "portrait"
        ]

        image = Image.open(image_path).convert('RGB')
        image_input = self.preprocess(image).unsqueeze(0)

        text_inputs = torch.cat([clip.tokenize(f"a photo of a {c}") for c in categories])

        with torch.no_grad():
            image_features = self.model.encode_image(image_input)
            text_features = self.model.encode_text(text_inputs)

            # Normalize features
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)

            # Calculate similarity
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            values, indices = similarity[0].topk(5)

        detections = []
        for value, index in zip(values, indices):
            if value.item() >= confidence:
                detections.append({
                    'name': categories[index],
                    'confidence': value.item(),
                    'bbox': None
                })

        return detections

    def get_primary_tags(self, image_path: str, max_tags: int = 5) -> List[str]:
        """Get primary object tags for image."""
        detections = self.detect_objects(image_path)

        # Sort by confidence and get top tags
        sorted_detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        return [d['name'] for d in sorted_detections[:max_tags]]


class ColorAnalyzer:
    """Analyzes image colors and extracts dominant colors."""

    def __init__(self):
        self.available = True

    def get_dominant_colors(self, image_path: str, num_colors: int = 5) -> List[Tuple[int, int, int]]:
        """
        Extract dominant colors from image.

        Returns:
            List of RGB tuples: [(R, G, B), ...]
        """
        try:
            # Use scikit-learn KMeans for color clustering
            from sklearn.cluster import KMeans

            # Load and resize image for faster processing
            img = Image.open(image_path).convert('RGB')
            img.thumbnail((200, 200))  # Resize for speed

            # Convert to numpy array and reshape
            pixels = np.array(img)
            pixels = pixels.reshape(-1, 3)

            # Perform K-means clustering
            kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
            kmeans.fit(pixels)

            # Get cluster centers (dominant colors)
            colors = kmeans.cluster_centers_.astype(int)
            return [tuple(color) for color in colors]

        except ImportError:
            # Fallback to simpler method without sklearn
            return self._get_dominant_colors_simple(image_path, num_colors)
        except Exception as e:
            logger.error(f"Color analysis failed: {e}")
            return []

    def _get_dominant_colors_simple(self, image_path: str, num_colors: int) -> List[Tuple[int, int, int]]:
        """Simple dominant color extraction using PIL."""
        try:
            img = Image.open(image_path).convert('RGB')
            img.thumbnail((50, 50))  # Very small for speed

            # Get all colors and count frequency
            colors = img.getcolors(maxcolors=10000)
            if not colors:
                return []

            # Sort by frequency and get top colors
            sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)
            return [color for count, color in sorted_colors[:num_colors]]

        except Exception as e:
            logger.error(f"Simple color analysis failed: {e}")
            return []

    def get_color_name(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB to human-readable color name."""
        r, g, b = rgb

        # Define color ranges
        if r > 200 and g > 200 and b > 200:
            return "white"
        elif r < 50 and g < 50 and b < 50:
            return "black"
        elif r > g and r > b:
            return "red"
        elif g > r and g > b:
            return "green"
        elif b > r and b > g:
            return "blue"
        elif r > 150 and g > 150 and b < 100:
            return "yellow"
        elif r > 150 and g < 100 and b > 150:
            return "magenta"
        elif r < 100 and g > 150 and b > 150:
            return "cyan"
        elif r > 150 and g > 100 and b < 100:
            return "orange"
        elif r > 100 and g < 100 and b > 100:
            return "purple"
        else:
            return "gray"

    def get_color_tags(self, image_path: str) -> List[str]:
        """Get color-based tags for image."""
        colors = self.get_dominant_colors(image_path, num_colors=3)
        return [self.get_color_name(color) for color in colors]


class FaceDetector:
    """Detects and recognizes faces in images."""

    def __init__(self):
        self.available = False
        self._initialize()
        self.known_faces = {}  # face_id -> encoding

    def _initialize(self):
        """Initialize face detection model."""
        try:
            import face_recognition
            self.available = True
            logger.info("Face detection initialized")
        except ImportError:
            logger.warning("face_recognition not available (install with: pip install face-recognition)")

    def detect_faces(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Detect faces in image.

        Returns:
            List of face detections with format:
            [{'bbox': [top, right, bottom, left], 'encoding': np.array, 'id': hash}, ...]
        """
        if not self.available:
            return []

        try:
            import face_recognition

            # Load image
            image = face_recognition.load_image_file(image_path)

            # Find faces
            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)

            faces = []
            for location, encoding in zip(face_locations, face_encodings):
                # Generate face ID from encoding
                face_id = hashlib.md5(encoding.tobytes()).hexdigest()[:8]

                faces.append({
                    'bbox': location,
                    'encoding': encoding,
                    'id': face_id
                })

            return faces

        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return []

    def get_face_count(self, image_path: str) -> int:
        """Get number of faces in image."""
        faces = self.detect_faces(image_path)
        return len(faces)

    def has_faces(self, image_path: str) -> bool:
        """Check if image contains faces."""
        return self.get_face_count(image_path) > 0


class SceneClassifier:
    """Classifies scene context (indoor/outdoor/nature/urban)."""

    def __init__(self):
        self.available = False
        self._initialize()

    def _initialize(self):
        """Initialize scene classification model."""
        try:
            # Try to use CLIP for scene classification
            import clip
            import torch
            self.model, self.preprocess = clip.load("ViT-B/32", device="cpu")
            self.available = True
            logger.info("Scene classification initialized (CLIP)")
        except ImportError:
            logger.warning("Scene classification not available (install clip)")

    def classify_scene(self, image_path: str) -> Dict[str, float]:
        """
        Classify image scene.

        Returns:
            Dict with scene probabilities: {'indoor': 0.8, 'outdoor': 0.2, ...}
        """
        if not self.available:
            return {}

        try:
            import torch
            import clip
            from PIL import Image

            # Scene categories
            categories = [
                "indoor scene",
                "outdoor scene",
                "nature landscape",
                "urban environment",
                "beach or water",
                "mountains",
                "forest",
                "cityscape",
                "room interior",
                "office space"
            ]

            image = Image.open(image_path).convert('RGB')
            image_input = self.preprocess(image).unsqueeze(0)

            text_inputs = torch.cat([clip.tokenize(f"a photo of {c}") for c in categories])

            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                text_features = self.model.encode_text(text_inputs)

                # Normalize
                image_features /= image_features.norm(dim=-1, keepdim=True)
                text_features /= text_features.norm(dim=-1, keepdim=True)

                # Calculate similarity
                similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)

            # Create result dictionary
            results = {}
            for i, category in enumerate(categories):
                results[category] = float(similarity[0][i].item())

            return results

        except Exception as e:
            logger.error(f"Scene classification failed: {e}")
            return {}

    def get_primary_scene(self, image_path: str) -> str:
        """Get primary scene classification."""
        scenes = self.classify_scene(image_path)
        if not scenes:
            return "unknown"

        return max(scenes.items(), key=lambda x: x[1])[0]


class QualityAnalyzer:
    """Analyzes image quality and resolution metrics."""

    def __init__(self):
        self.available = True

    def analyze_quality(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze image quality metrics.

        Returns:
            Dict with quality metrics: {
                'resolution': (width, height),
                'megapixels': float,
                'aspect_ratio': str,
                'file_size_mb': float,
                'format': str,
                'mode': str,
                'sharpness_score': float,
                'brightness_score': float
            }
        """
        try:
            img = Image.open(image_path)
            width, height = img.size
            megapixels = (width * height) / 1_000_000

            # Calculate aspect ratio
            from math import gcd
            divisor = gcd(width, height)
            aspect_w = width // divisor
            aspect_h = height // divisor
            aspect_ratio = f"{aspect_w}:{aspect_h}"

            # Common aspect ratios
            if abs(width/height - 16/9) < 0.1:
                aspect_ratio = "16:9"
            elif abs(width/height - 4/3) < 0.1:
                aspect_ratio = "4:3"
            elif abs(width/height - 1) < 0.1:
                aspect_ratio = "1:1"

            # File size
            file_size_mb = Path(image_path).stat().st_size / (1024**2)

            # Calculate sharpness (Laplacian variance)
            sharpness = self._calculate_sharpness(img)

            # Calculate brightness
            brightness = self._calculate_brightness(img)

            return {
                'resolution': (width, height),
                'megapixels': round(megapixels, 2),
                'aspect_ratio': aspect_ratio,
                'file_size_mb': round(file_size_mb, 2),
                'format': img.format or 'unknown',
                'mode': img.mode,
                'sharpness_score': round(sharpness, 2),
                'brightness_score': round(brightness, 2)
            }

        except Exception as e:
            logger.error(f"Quality analysis failed: {e}")
            return {}

    def _calculate_sharpness(self, img: Image.Image) -> float:
        """Calculate image sharpness using Laplacian variance."""
        try:
            # Convert to grayscale
            gray = img.convert('L')
            gray_array = np.array(gray)

            # Simple edge detection (approximate Laplacian)
            laplacian = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])

            # Calculate variance (measure of sharpness)
            from scipy import signal
            edges = signal.convolve2d(gray_array, laplacian, mode='same')
            variance = np.var(edges)

            # Normalize to 0-100 scale
            return min(100, variance / 10)

        except ImportError:
            # Fallback without scipy
            gray = img.convert('L')
            gray_array = np.array(gray)

            # Simple gradient-based sharpness
            dx = np.diff(gray_array, axis=1)
            dy = np.diff(gray_array, axis=0)
            variance = np.var(dx) + np.var(dy)

            return min(100, variance / 10)

        except Exception:
            return 0.0

    def _calculate_brightness(self, img: Image.Image) -> float:
        """Calculate average brightness (0-100)."""
        try:
            gray = img.convert('L')
            pixels = np.array(gray)
            return float(np.mean(pixels)) / 255 * 100
        except Exception:
            return 50.0

    def get_resolution_category(self, image_path: str) -> str:
        """Categorize image by resolution."""
        metrics = self.analyze_quality(image_path)
        if not metrics:
            return "unknown"

        width, height = metrics['resolution']
        total_pixels = width * height

        if total_pixels >= 8_000_000:  # 8MP+
            return "high_resolution"
        elif total_pixels >= 2_000_000:  # 2-8MP
            return "medium_resolution"
        else:
            return "low_resolution"


class VideoSceneDetector:
    """Detects scene changes in videos and extracts key frames."""

    def __init__(self):
        self.available = False
        self._initialize()

    def _initialize(self):
        """Initialize video scene detection."""
        try:
            import cv2
            self.available = True
            logger.info("Video scene detection initialized")
        except ImportError:
            logger.warning("OpenCV not available for video scene detection")

    def detect_scenes(self, video_path: str, threshold: float = 30.0) -> List[Dict[str, Any]]:
        """
        Detect scene changes in video.

        Returns:
            List of scene information: [
                {'frame_number': 100, 'timestamp': 3.33, 'scene_id': 0},
                ...
            ]
        """
        if not self.available:
            return []

        try:
            import cv2

            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)

            scenes = []
            prev_frame = None
            frame_number = 0
            scene_id = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Convert to grayscale for comparison
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                if prev_frame is not None:
                    # Calculate frame difference
                    diff = cv2.absdiff(prev_frame, gray)
                    diff_score = np.mean(diff)

                    # Detect scene change
                    if diff_score > threshold:
                        scenes.append({
                            'frame_number': frame_number,
                            'timestamp': frame_number / fps,
                            'scene_id': scene_id
                        })
                        scene_id += 1

                prev_frame = gray
                frame_number += 1

            cap.release()
            return scenes

        except Exception as e:
            logger.error(f"Video scene detection failed: {e}")
            return []

    def extract_key_frames(self, video_path: str, num_frames: int = 10) -> List[str]:
        """Extract key frames from video evenly distributed."""
        if not self.available:
            return []

        try:
            import cv2

            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            interval = max(1, total_frames // num_frames)
            key_frames = []

            temp_dir = Path.home() / "AppData" / "Local" / "Temp" / "key_frames"
            temp_dir.mkdir(parents=True, exist_ok=True)

            for i in range(num_frames):
                frame_pos = min(i * interval, total_frames - 1)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                ret, frame = cap.read()

                if ret:
                    frame_path = temp_dir / f"frame_{i}.jpg"
                    cv2.imwrite(str(frame_path), frame)
                    key_frames.append(str(frame_path))

            cap.release()
            return key_frames

        except Exception as e:
            logger.error(f"Key frame extraction failed: {e}")
            return []


class AudioTranscriber:
    """Transcribes and analyzes audio files."""

    def __init__(self):
        self.available = False
        self._initialize()

    def _initialize(self):
        """Initialize audio transcription model."""
        try:
            import whisper
            self.model = whisper.load_model("base")  # Use base model for speed
            self.available = True
            logger.info("Audio transcription initialized (Whisper)")
        except ImportError:
            logger.warning("Whisper not available (install with: pip install openai-whisper)")

    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file.

        Returns:
            Dict with transcription: {
                'text': str,
                'language': str,
                'duration': float,
                'confidence': float
            }
        """
        if not self.available:
            return {}

        try:
            import whisper

            result = self.model.transcribe(audio_path)

            return {
                'text': result.get('text', ''),
                'language': result.get('language', 'unknown'),
                'segments': len(result.get('segments', [])),
            }

        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return {}

    def detect_audio_type(self, audio_path: str) -> str:
        """Detect if audio is music, speech, or mixed."""
        # This is a simplified detection - could be enhanced with librosa
        transcription = self.transcribe_audio(audio_path)

        if not transcription:
            return "unknown"

        text = transcription.get('text', '').strip()

        if len(text) > 100:
            return "speech"
        elif len(text) < 20:
            return "music"
        else:
            return "mixed"


class AIFeatureManager:
    """Central manager for all AI features."""

    def __init__(self):
        """Initialize all AI feature modules."""
        self.object_detector = ObjectDetector()
        self.color_analyzer = ColorAnalyzer()
        self.face_detector = FaceDetector()
        self.scene_classifier = SceneClassifier()
        self.quality_analyzer = QualityAnalyzer()
        self.video_scene_detector = VideoSceneDetector()
        self.audio_transcriber = AudioTranscriber()

    def analyze_image(self, image_path: str, features: Dict[str, bool]) -> Dict[str, Any]:
        """
        Analyze image with selected AI features.

        Args:
            image_path: Path to image file
            features: Dict of feature flags: {'object_detection': True, 'color_analysis': True, ...}

        Returns:
            Dict with all analysis results
        """
        results = {}

        if features.get('object_detection') and self.object_detector.available:
            results['objects'] = self.object_detector.get_primary_tags(image_path)

        if features.get('color_analysis'):
            results['colors'] = self.color_analyzer.get_color_tags(image_path)
            results['dominant_colors'] = self.color_analyzer.get_dominant_colors(image_path)

        if features.get('face_detection') and self.face_detector.available:
            faces = self.face_detector.detect_faces(image_path)
            results['face_count'] = len(faces)
            results['has_faces'] = len(faces) > 0

        if features.get('scene_classification') and self.scene_classifier.available:
            results['scene'] = self.scene_classifier.get_primary_scene(image_path)
            results['scene_scores'] = self.scene_classifier.classify_scene(image_path)

        if features.get('quality_metrics'):
            results['quality'] = self.quality_analyzer.analyze_quality(image_path)
            results['resolution_category'] = self.quality_analyzer.get_resolution_category(image_path)

        return results

    def get_available_features(self) -> Dict[str, bool]:
        """Get availability status of all AI features."""
        return {
            'object_detection': self.object_detector.available,
            'color_analysis': self.color_analyzer.available,
            'face_detection': self.face_detector.available,
            'scene_classification': self.scene_classifier.available,
            'quality_metrics': self.quality_analyzer.available,
            'video_scene_detection': self.video_scene_detector.available,
            'audio_transcription': self.audio_transcriber.available
        }
