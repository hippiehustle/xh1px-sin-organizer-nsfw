#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Media Scanner ULTRA BUFF v3.0
Extends base scanner with comprehensive AI features and advanced organization

New Features:
- Object detection and auto-tagging
- Color-based analysis and sorting
- Face detection and recognition
- Scene classification (indoor/outdoor/nature)
- Quality and resolution metrics
- Video scene detection
- Audio transcription
- Date-based folder hierarchies
- Custom naming templates
- Multi-criteria organization
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Import base scanner
from media_scanner import (
    EnhancedMediaScanner, FileInfo, DetectionResult,
    ScannerConfig, FileOrganizer
)

# Import AI features
from ai_features import AIFeatureManager

logger = logging.getLogger(__name__)


class UltraEnhancedMediaScanner(EnhancedMediaScanner):
    """
    Ultra-buffed media scanner with comprehensive AI features.

    Extends base EnhancedMediaScanner with:
    - AI object detection and tagging
    - Color analysis and dominant color extraction
    - Face detection and recognition
    - Scene classification
    - Quality and resolution metrics
    - Video scene detection
    - Audio transcription
    - Advanced organization methods
    """

    def __init__(self, use_visual_analysis: bool = True, max_workers: int = 4,
                 ai_features: Optional[Dict[str, bool]] = None):
        """
        Initialize ultra-enhanced scanner.

        Args:
            use_visual_analysis: Enable NSFW visual detection
            max_workers: Number of parallel workers
            ai_features: Dict of AI features to enable:
                {
                    'object_detection': True,
                    'color_analysis': True,
                    'face_detection': False,
                    'scene_classification': True,
                    'quality_metrics': True,
                    'video_scene_detection': False,
                    'audio_transcription': False
                }
        """
        # Initialize base scanner
        super().__init__(use_visual_analysis, max_workers)

        # AI features configuration
        self.ai_features = ai_features or {}

        # Initialize AI feature manager
        self.ai_manager = AIFeatureManager()

        # Log available AI features
        available = self.ai_manager.get_available_features()
        enabled_features = [k for k, v in self.ai_features.items() if v]

        logger.info(f"AI Features - Available: {available}")
        logger.info(f"AI Features - Enabled: {enabled_features}")

        # Extended results storage for AI data
        self.results['ai_analysis'] = {
            'objects_detected': {},
            'colors_detected': {},
            'faces_found': 0,
            'scenes_classified': {},
            'quality_analysis': {}
        }

    def process_file(self, filepath: Path) -> Optional[tuple]:
        """
        Enhanced file processing with AI features.

        Extends base process_file with AI analysis.
        """
        # Get base processing result
        base_result = super().process_file(filepath)

        if not base_result:
            return None

        media_type, classification, file_info = base_result

        # Apply AI enhancements if enabled
        if self.ai_features:
            ai_data = self._apply_ai_analysis(filepath, media_type)

            # Add AI data to file_info object (dynamically add attribute)
            file_info.ai_data = ai_data

            # Update classification based on AI analysis
            classification = self._refine_classification(classification, ai_data)

            # Update aggregated AI statistics
            self._update_ai_stats(ai_data, media_type)

            return media_type, classification, file_info

        return base_result

    def _apply_ai_analysis(self, filepath: Path, media_type: str) -> Dict[str, Any]:
        """Apply enabled AI features to file."""
        ai_data = {}

        try:
            if media_type == 'images':
                ai_data = self.ai_manager.analyze_image(str(filepath), self.ai_features)

            elif media_type == 'videos' and self.ai_features.get('video_scene_detection'):
                if self.ai_manager.video_scene_detector.available:
                    scenes = self.ai_manager.video_scene_detector.detect_scenes(str(filepath))
                    ai_data['video_scenes'] = len(scenes)
                    ai_data['scene_changes'] = scenes[:5]  # Store first 5 scene changes

            elif media_type == 'audio' and self.ai_features.get('audio_transcription'):
                if self.ai_manager.audio_transcriber.available:
                    transcription = self.ai_manager.audio_transcriber.transcribe_audio(str(filepath))
                    ai_data['audio_type'] = self.ai_manager.audio_transcriber.detect_audio_type(str(filepath))
                    ai_data['transcription_preview'] = transcription.get('text', '')[:200]

        except Exception as e:
            logger.error(f"AI analysis failed for {filepath}: {e}")
            ai_data['error'] = str(e)

        return ai_data

    def _refine_classification(self, classification: str, ai_data: Dict[str, Any]) -> str:
        """
        Refine classification using AI analysis results.

        Can upgrade 'uncertain' classifications to more specific categories
        based on AI insights.
        """
        # If already classified as NSFW or SFW, keep it
        if classification in ['nsfw', 'sfw']:
            return classification

        # Use AI data to refine uncertain classifications
        if classification == 'uncertain':
            # Check for strong SFW indicators
            if ai_data.get('objects'):
                safe_objects = {'person', 'car', 'dog', 'cat', 'building', 'tree', 'food'}
                detected = set(ai_data['objects'])
                if detected & safe_objects:
                    return 'sfw'

            # Check scene classification
            if ai_data.get('scene'):
                safe_scenes = ['indoor scene', 'nature landscape', 'office space']
                if any(safe in ai_data['scene'] for safe in safe_scenes):
                    return 'sfw'

        return classification

    def _update_ai_stats(self, ai_data: Dict[str, Any], media_type: str):
        """Update aggregated AI statistics."""
        # Count objects
        if 'objects' in ai_data:
            for obj in ai_data['objects']:
                self.results['ai_analysis']['objects_detected'][obj] = \
                    self.results['ai_analysis']['objects_detected'].get(obj, 0) + 1

        # Count colors
        if 'colors' in ai_data:
            for color in ai_data['colors']:
                self.results['ai_analysis']['colors_detected'][color] = \
                    self.results['ai_analysis']['colors_detected'].get(color, 0) + 1

        # Count faces
        if 'face_count' in ai_data:
            self.results['ai_analysis']['faces_found'] += ai_data['face_count']

        # Count scenes
        if 'scene' in ai_data:
            scene = ai_data['scene']
            self.results['ai_analysis']['scenes_classified'][scene] = \
                self.results['ai_analysis']['scenes_classified'].get(scene, 0) + 1

    def organize_files_advanced(self, output_base: Path, config: Dict[str, Any]) -> None:
        """
        Advanced file organization with AI-based sorting.

        Args:
            output_base: Base directory for organized files
            config: Organization configuration:
                {
                    'mode': 'copy' | 'move' | 'skip' | 'symlink',
                    'organize_by': 'classification' | 'type' | 'date' | 'color' | 'tags' | 'quality',
                    'date_hierarchy': True | False,
                    'keep_structure': True | False,
                    'naming_template': '{original}' | '{date}_{original}' | etc.
                }
        """
        mode = config.get('mode', 'skip')
        if mode == 'skip':
            return

        organize_by = config.get('organize_by', 'classification')
        date_hierarchy = config.get('date_hierarchy', False)
        naming_template = config.get('naming_template', '{original}')

        logger.info(f"Advanced organization: {organize_by}, date_hierarchy={date_hierarchy}")
        print(f"\n[*] Organizing files by: {organize_by}")

        organized_count = 0
        failed_count = 0

        # Iterate through all files
        for media_type in ['images', 'videos', 'audio']:
            for category in ['sfw', 'nsfw', 'uncertain']:
                files = self.results[media_type][category]

                for file_info in files:
                    try:
                        # Convert FileInfo to dict if needed
                        if hasattr(file_info, 'to_dict'):
                            file_info_dict = file_info.to_dict()
                            # Preserve ai_data if it exists
                            if hasattr(file_info, 'ai_data'):
                                file_info_dict['ai_data'] = file_info.ai_data
                        else:
                            file_info_dict = file_info

                        src_path = Path(file_info_dict['path'])

                        if not src_path.exists():
                            failed_count += 1
                            continue

                        # Determine destination path based on organization method
                        dest_path = self._calculate_dest_path(
                            src_path, file_info_dict, output_base,
                            organize_by, category, media_type,
                            date_hierarchy, naming_template
                        )

                        # Ensure unique path
                        dest_path = self._ensure_unique_path(dest_path)

                        # Transfer file
                        if self._transfer_file_with_mode(src_path, dest_path, mode):
                            organized_count += 1
                        else:
                            failed_count += 1

                    except Exception as e:
                        path = file_info_dict.get('path', 'unknown') if 'file_info_dict' in locals() else 'unknown'
                        logger.error(f"Error organizing {path}: {e}")
                        failed_count += 1

        print(f"\n[+] Organization complete!")
        print(f"[+] Successfully organized: {organized_count} files")
        if failed_count > 0:
            print(f"[!] Failed: {failed_count} files")

    def _calculate_dest_path(self, src_path: Path, file_info: Dict[str, Any],
                            output_base: Path, organize_by: str, category: str,
                            media_type: str, date_hierarchy: bool,
                            naming_template: str) -> Path:
        """Calculate destination path based on organization method."""

        # Start with base directory
        dest_dir = output_base

        # Add organization-specific folders
        if organize_by == 'classification':
            dest_dir = dest_dir / media_type / category

        elif organize_by == 'type':
            dest_dir = dest_dir / media_type / category

        elif organize_by == 'date':
            # Use file modification date
            modified = file_info.get('modified', datetime.now().isoformat())
            try:
                dt = datetime.fromisoformat(modified)
            except:
                dt = datetime.now()

            if date_hierarchy:
                dest_dir = dest_dir / str(dt.year) / f"{dt.month:02d}" / f"{dt.day:02d}"
            else:
                dest_dir = dest_dir / dt.strftime("%Y-%m-%d")

        elif organize_by == 'color':
            # Use dominant color
            ai_data = file_info.get('ai_data', {})
            colors = ai_data.get('colors', [])
            primary_color = colors[0] if colors else 'unknown'
            dest_dir = dest_dir / media_type / primary_color

        elif organize_by == 'tags':
            # Use object tags
            ai_data = file_info.get('ai_data', {})
            objects = ai_data.get('objects', [])
            primary_tag = objects[0] if objects else 'untagged'
            dest_dir = dest_dir / media_type / primary_tag

        elif organize_by == 'quality':
            # Use quality/resolution category
            ai_data = file_info.get('ai_data', {})
            quality = ai_data.get('quality', {})
            resolution_cat = quality.get('resolution_category', 'unknown') if quality else 'unknown'
            dest_dir = dest_dir / media_type / resolution_cat

        elif organize_by == 'scene':
            # Use scene classification
            ai_data = file_info.get('ai_data', {})
            scene = ai_data.get('scene', 'unknown')
            dest_dir = dest_dir / media_type / scene.replace(' ', '_')

        # Apply naming template
        filename = self._apply_naming_template(src_path, file_info, naming_template)

        return dest_dir / filename

    def _apply_naming_template(self, src_path: Path, file_info: Dict[str, Any],
                               template: str) -> str:
        """Apply naming template to generate new filename."""

        # Parse template
        if template == '{original}':
            return src_path.name

        # Get file metadata
        modified = file_info.get('modified', datetime.now().isoformat())
        try:
            dt = datetime.fromisoformat(modified)
            date_str = dt.strftime("%Y%m%d")
        except:
            date_str = datetime.now().strftime("%Y%m%d")

        # Get AI data
        ai_data = file_info.get('ai_data', {})

        # Determine classification
        detection = file_info.get('detection_data', {})
        classification = 'unknown'
        if isinstance(detection, dict):
            max_conf = detection.get('max_confidence', 0)
            if max_conf > 0.6:
                classification = 'nsfw'
            else:
                classification = 'sfw'

        # Get media type
        ext = src_path.suffix.lower()
        if ext in self.image_extensions:
            media_type = 'image'
        elif ext in self.video_extensions:
            media_type = 'video'
        elif ext in self.audio_extensions:
            media_type = 'audio'
        else:
            media_type = 'file'

        # Get primary tag
        objects = ai_data.get('objects', [])
        tag = objects[0] if objects else 'file'

        # Replace placeholders
        filename = template
        filename = filename.replace('{original}', src_path.stem)
        filename = filename.replace('{date}', date_str)
        filename = filename.replace('{type}', media_type)
        filename = filename.replace('{classification}', classification)
        filename = filename.replace('{tag}', tag)
        filename = filename.replace('{counter}', '001')  # Will be incremented if duplicate

        return filename + src_path.suffix

    def _ensure_unique_path(self, dest_path: Path) -> Path:
        """Ensure destination path is unique by adding counter if needed."""
        if not dest_path.exists():
            return dest_path

        counter = 1
        while True:
            new_name = f"{dest_path.stem}_{counter}{dest_path.suffix}"
            new_path = dest_path.parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1

    def _transfer_file_with_mode(self, src_path: Path, dest_path: Path, mode: str) -> bool:
        """Transfer file according to mode (copy/move/symlink)."""
        import shutil

        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            if mode == 'copy':
                shutil.copy2(str(src_path), str(dest_path))
            elif mode == 'move':
                shutil.move(str(src_path), str(dest_path))
            elif mode == 'symlink':
                # Create symbolic link
                if os.name == 'nt':  # Windows
                    # Use junction point for directories, symlink for files
                    os.symlink(str(src_path.absolute()), str(dest_path))
                else:
                    dest_path.symlink_to(src_path.absolute())

            return True

        except Exception as e:
            logger.error(f"Transfer failed ({mode}): {src_path} -> {dest_path}: {e}")
            return False

    def generate_report(self, output_dir: Path) -> tuple:
        """
        Generate enhanced report with AI analysis data.

        Extends base report with AI insights.
        """
        # Generate base report
        report_file, summary_file = super().generate_report(output_dir)

        # Generate AI analysis report
        ai_report_file = self._generate_ai_report(output_dir)

        return report_file, summary_file, ai_report_file

    def _generate_ai_report(self, output_dir: Path) -> Path:
        """Generate separate AI analysis report."""
        import json

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ai_report_file = output_dir / f'ai_analysis_{timestamp}.json'

        ai_summary = {
            'timestamp': timestamp,
            'features_enabled': self.ai_features,
            'features_available': self.ai_manager.get_available_features(),
            'analysis_results': self.results['ai_analysis'],
            'top_objects': sorted(
                self.results['ai_analysis']['objects_detected'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:20],
            'top_colors': sorted(
                self.results['ai_analysis']['colors_detected'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            'top_scenes': sorted(
                self.results['ai_analysis']['scenes_classified'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

        with open(ai_report_file, 'w', encoding='utf-8') as f:
            json.dump(ai_summary, f, indent=2, ensure_ascii=False)

        logger.info(f"AI analysis report saved to {ai_report_file}")

        # Print AI summary
        print("\n" + "="*70)
        print("AI ANALYSIS SUMMARY")
        print("="*70)

        if ai_summary['top_objects']:
            print("\nTop Detected Objects:")
            for obj, count in ai_summary['top_objects'][:10]:
                print(f"  {obj}: {count}")

        if ai_summary['top_colors']:
            print("\nTop Colors:")
            for color, count in ai_summary['top_colors'][:5]:
                print(f"  {color}: {count}")

        if ai_summary['top_scenes']:
            print("\nTop Scenes:")
            for scene, count in ai_summary['top_scenes'][:5]:
                print(f"  {scene}: {count}")

        if self.results['ai_analysis']['faces_found'] > 0:
            print(f"\nTotal Faces Detected: {self.results['ai_analysis']['faces_found']}")

        print("="*70)

        return ai_report_file


def create_scanner_from_config(config: Dict[str, Any]) -> UltraEnhancedMediaScanner:
    """
    Factory function to create scanner from GUI configuration.

    Args:
        config: Configuration dictionary from GUI

    Returns:
        Configured UltraEnhancedMediaScanner instance
    """
    # Extract AI features
    ai_features = {
        'object_detection': config.get('object_detection', False),
        'color_analysis': config.get('color_analysis', False),
        'face_detection': config.get('face_detection', False),
        'scene_classification': config.get('scene_classification', False),
        'quality_metrics': config.get('quality_metrics', False),
        'video_scene_detection': config.get('video_scene_detection', False),
        'audio_transcription': config.get('audio_transcription', False)
    }

    # Create scanner
    scanner = UltraEnhancedMediaScanner(
        use_visual_analysis=config.get('nsfw_detection', True),
        max_workers=config.get('workers', 4),
        ai_features=ai_features
    )

    # Configure scanner
    scanner.CONFIDENCE_THRESHOLD = config.get('confidence_threshold', 0.6)

    # Apply video settings
    video_size = config.get('video_size_limit', '500MB')
    # Parse video size (simplified)
    if video_size.endswith('MB'):
        scanner.VIDEO_SIZE_LIMIT = int(video_size[:-2]) * 1024 * 1024
    elif video_size.endswith('GB'):
        scanner.VIDEO_SIZE_LIMIT = int(video_size[:-2]) * 1024 * 1024 * 1024

    return scanner


if __name__ == "__main__":
    # Example usage
    print("Enhanced Media Scanner ULTRA BUFF v3.0")
    print("=" * 70)
    print("This module provides AI-enhanced scanning capabilities.")
    print("Use via GUI (run_gui.bat) or import in your own scripts.")
    print("=" * 70)
