#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Media Scanner GUI - Ultra BUFF Edition v3.0
Modern tkinter interface with comprehensive scanning customization

Features:
- 50+ configurable scanning options
- AI-powered sorting (objects, faces, scenes, colors)
- Advanced file filtering and organization
- Real-time preview and validation
- Configuration profiles with save/load
- Progress tracking with live updates
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import json
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TooltipHelper:
    """Provides tooltip hover functionality for widgets."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        """Display tooltip near widget."""
        if self.tooltip_window or not self.text:
            return

        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(tw, text=self.text, justify='left',
                        background="#ffffe0", relief='solid', borderwidth=1,
                        font=("Segoe UI", 9))
        label.pack()

    def hide_tooltip(self, event=None):
        """Hide tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class ConfigurationProfile:
    """Manages configuration profiles for save/load functionality."""

    def __init__(self, profiles_dir: Path = None):
        self.profiles_dir = profiles_dir or (Path.home() / ".media_scanner" / "profiles")
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def save_profile(self, name: str, config: Dict[str, Any]) -> bool:
        """Save configuration profile to disk."""
        try:
            profile_file = self.profiles_dir / f"{name}.json"
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving profile: {e}")
            return False

    def load_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Load configuration profile from disk."""
        try:
            profile_file = self.profiles_dir / f"{name}.json"
            if profile_file.exists():
                with open(profile_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading profile: {e}")
        return None

    def list_profiles(self) -> List[str]:
        """List all available profile names."""
        try:
            return [f.stem for f in self.profiles_dir.glob("*.json")]
        except Exception:
            return []

    def delete_profile(self, name: str) -> bool:
        """Delete a configuration profile."""
        try:
            profile_file = self.profiles_dir / f"{name}.json"
            if profile_file.exists():
                profile_file.unlink()
                return True
        except Exception as e:
            print(f"Error deleting profile: {e}")
        return False


class ScanConfigFrame(ttk.LabelFrame):
    """Frame containing scan path and basic options."""

    def __init__(self, parent):
        super().__init__(parent, text="📂 Scanning Configuration", padding=10)
        self.create_widgets()

    def create_widgets(self):
        # Scan path selection
        ttk.Label(self, text="Scan Path:").grid(row=0, column=0, sticky='w', pady=5)
        self.scan_path_var = tk.StringVar(value=str(Path.home()))
        scan_path_entry = ttk.Entry(self, textvariable=self.scan_path_var, width=50)
        scan_path_entry.grid(row=0, column=1, padx=5, pady=5)

        browse_btn = ttk.Button(self, text="Browse...", command=self.browse_scan_path)
        browse_btn.grid(row=0, column=2, padx=5)
        TooltipHelper(browse_btn, "Select folder to scan")

        # Recursive scanning
        self.recursive_var = tk.BooleanVar(value=True)
        recursive_cb = ttk.Checkbutton(self, text="Scan subdirectories recursively",
                                       variable=self.recursive_var)
        recursive_cb.grid(row=1, column=1, sticky='w', pady=5)
        TooltipHelper(recursive_cb, "Include all subfolders in scan")

        # Max files limit
        ttk.Label(self, text="Max Files:").grid(row=2, column=0, sticky='w', pady=5)
        self.max_files_var = tk.StringVar(value="")
        max_files_entry = ttk.Entry(self, textvariable=self.max_files_var, width=20)
        max_files_entry.grid(row=2, column=1, sticky='w', padx=5, pady=5)
        TooltipHelper(max_files_entry, "Leave empty for unlimited, or enter max number of files to scan")

        # Max depth
        ttk.Label(self, text="Max Depth:").grid(row=3, column=0, sticky='w', pady=5)
        self.max_depth_var = tk.StringVar(value="")
        max_depth_entry = ttk.Entry(self, textvariable=self.max_depth_var, width=20)
        max_depth_entry.grid(row=3, column=1, sticky='w', padx=5, pady=5)
        TooltipHelper(max_depth_entry, "Maximum folder depth to scan (empty = unlimited)")

    def browse_scan_path(self):
        """Open folder browser dialog."""
        folder = filedialog.askdirectory(initialdir=self.scan_path_var.get(),
                                        title="Select folder to scan")
        if folder:
            self.scan_path_var.set(folder)

    def get_config(self) -> Dict[str, Any]:
        """Extract configuration from widgets."""
        max_files = self.max_files_var.get().strip()
        max_depth = self.max_depth_var.get().strip()

        return {
            'scan_path': self.scan_path_var.get(),
            'recursive': self.recursive_var.get(),
            'max_files': int(max_files) if max_files else None,
            'max_depth': int(max_depth) if max_depth else None
        }

    def set_config(self, config: Dict[str, Any]):
        """Apply configuration to widgets."""
        self.scan_path_var.set(config.get('scan_path', str(Path.home())))
        self.recursive_var.set(config.get('recursive', True))

        max_files = config.get('max_files')
        self.max_files_var.set(str(max_files) if max_files else "")

        max_depth = config.get('max_depth')
        self.max_depth_var.set(str(max_depth) if max_depth else "")


class FileFilterFrame(ttk.LabelFrame):
    """Frame for file filtering options."""

    def __init__(self, parent):
        super().__init__(parent, text="🔍 File Filtering", padding=10)
        self.create_widgets()

    def create_widgets(self):
        # File size filters
        ttk.Label(self, text="Min Size:").grid(row=0, column=0, sticky='w', pady=5)
        self.min_size_var = tk.StringVar(value="")
        min_size_entry = ttk.Entry(self, textvariable=self.min_size_var, width=15)
        min_size_entry.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        ttk.Label(self, text="(e.g., 1MB, 500KB)").grid(row=0, column=2, sticky='w')
        TooltipHelper(min_size_entry, "Minimum file size (1KB, 1MB, 1GB)")

        ttk.Label(self, text="Max Size:").grid(row=1, column=0, sticky='w', pady=5)
        self.max_size_var = tk.StringVar(value="")
        max_size_entry = ttk.Entry(self, textvariable=self.max_size_var, width=15)
        max_size_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        ttk.Label(self, text="(e.g., 100MB, 1GB)").grid(row=1, column=2, sticky='w')
        TooltipHelper(max_size_entry, "Maximum file size (1KB, 1MB, 1GB)")

        # Extension filters
        ttk.Label(self, text="Extensions:").grid(row=2, column=0, sticky='w', pady=5)
        self.extensions_var = tk.StringVar(value="")
        ext_entry = ttk.Entry(self, textvariable=self.extensions_var, width=30)
        ext_entry.grid(row=2, column=1, columnspan=2, sticky='w', padx=5, pady=5)
        TooltipHelper(ext_entry, "Include only these extensions (e.g., jpg,png,mp4) - leave empty for all")

        ttk.Label(self, text="Exclude Ext:").grid(row=3, column=0, sticky='w', pady=5)
        self.exclude_ext_var = tk.StringVar(value="")
        exclude_ext_entry = ttk.Entry(self, textvariable=self.exclude_ext_var, width=30)
        exclude_ext_entry.grid(row=3, column=1, columnspan=2, sticky='w', padx=5, pady=5)
        TooltipHelper(exclude_ext_entry, "Exclude these extensions (e.g., tmp,bak)")

        # Date filters
        ttk.Label(self, text="Modified After:").grid(row=4, column=0, sticky='w', pady=5)
        self.modified_after_var = tk.StringVar(value="")
        after_entry = ttk.Entry(self, textvariable=self.modified_after_var, width=15)
        after_entry.grid(row=4, column=1, sticky='w', padx=5, pady=5)
        ttk.Label(self, text="(YYYY-MM-DD)").grid(row=4, column=2, sticky='w')
        TooltipHelper(after_entry, "Only files modified after this date")

        ttk.Label(self, text="Modified Before:").grid(row=5, column=0, sticky='w', pady=5)
        self.modified_before_var = tk.StringVar(value="")
        before_entry = ttk.Entry(self, textvariable=self.modified_before_var, width=15)
        before_entry.grid(row=5, column=1, sticky='w', padx=5, pady=5)
        ttk.Label(self, text="(YYYY-MM-DD)").grid(row=5, column=2, sticky='w')
        TooltipHelper(before_entry, "Only files modified before this date")

    def get_config(self) -> Dict[str, Any]:
        """Extract configuration from widgets."""
        return {
            'min_size': self.min_size_var.get().strip() or None,
            'max_size': self.max_size_var.get().strip() or None,
            'extensions': self.extensions_var.get().strip() or None,
            'exclude_extensions': self.exclude_ext_var.get().strip() or None,
            'modified_after': self.modified_after_var.get().strip() or None,
            'modified_before': self.modified_before_var.get().strip() or None
        }

    def set_config(self, config: Dict[str, Any]):
        """Apply configuration to widgets."""
        self.min_size_var.set(config.get('min_size', '') or '')
        self.max_size_var.set(config.get('max_size', '') or '')
        self.extensions_var.set(config.get('extensions', '') or '')
        self.exclude_ext_var.set(config.get('exclude_extensions', '') or '')
        self.modified_after_var.set(config.get('modified_after', '') or '')
        self.modified_before_var.set(config.get('modified_before', '') or '')


class AIFeaturesFrame(ttk.LabelFrame):
    """Frame for AI-powered analysis features."""

    def __init__(self, parent):
        super().__init__(parent, text="🤖 AI-Powered Features", padding=10)
        self.create_widgets()

    def create_widgets(self):
        # Visual NSFW detection
        self.nsfw_detection_var = tk.BooleanVar(value=True)
        nsfw_cb = ttk.Checkbutton(self, text="Enable NSFW Visual Detection (NudeNet)",
                                  variable=self.nsfw_detection_var,
                                  command=self.toggle_nsfw_options)
        nsfw_cb.grid(row=0, column=0, columnspan=3, sticky='w', pady=5)
        TooltipHelper(nsfw_cb, "Use AI to detect explicit content in images/videos")

        # NSFW confidence threshold
        ttk.Label(self, text="  Confidence Threshold:").grid(row=1, column=0, sticky='w', pady=5)
        self.confidence_var = tk.DoubleVar(value=0.6)
        self.confidence_scale = ttk.Scale(self, from_=0.1, to=0.9, orient='horizontal',
                                         variable=self.confidence_var, length=200)
        self.confidence_scale.grid(row=1, column=1, padx=5, pady=5)
        self.confidence_label = ttk.Label(self, text="0.60")
        self.confidence_label.grid(row=1, column=2, sticky='w')
        self.confidence_var.trace('w', self.update_confidence_label)
        TooltipHelper(self.confidence_scale, "Lower = more sensitive (more detections)")

        # Object detection and tagging
        self.object_detection_var = tk.BooleanVar(value=False)
        obj_cb = ttk.Checkbutton(self, text="Object Detection & Auto-Tagging (YOLO/CLIP)",
                                variable=self.object_detection_var)
        obj_cb.grid(row=2, column=0, columnspan=3, sticky='w', pady=5)
        TooltipHelper(obj_cb, "Detect objects like cars, animals, people for automatic tagging")

        # Color analysis
        self.color_analysis_var = tk.BooleanVar(value=False)
        color_cb = ttk.Checkbutton(self, text="Color Analysis & Dominant Color Extraction",
                                   variable=self.color_analysis_var)
        color_cb.grid(row=3, column=0, columnspan=3, sticky='w', pady=5)
        TooltipHelper(color_cb, "Extract dominant colors for color-based organization")

        # Face detection
        self.face_detection_var = tk.BooleanVar(value=False)
        face_cb = ttk.Checkbutton(self, text="Face Detection & Recognition",
                                 variable=self.face_detection_var)
        face_cb.grid(row=4, column=0, columnspan=3, sticky='w', pady=5)
        TooltipHelper(face_cb, "Detect and group photos by people's faces")

        # Scene classification
        self.scene_classification_var = tk.BooleanVar(value=False)
        scene_cb = ttk.Checkbutton(self, text="Scene Classification (Indoor/Outdoor/Nature)",
                                  variable=self.scene_classification_var)
        scene_cb.grid(row=5, column=0, columnspan=3, sticky='w', pady=5)
        TooltipHelper(scene_cb, "Classify images by scene context")

        # Quality metrics
        self.quality_metrics_var = tk.BooleanVar(value=False)
        quality_cb = ttk.Checkbutton(self, text="Quality & Resolution Metrics",
                                    variable=self.quality_metrics_var)
        quality_cb.grid(row=6, column=0, columnspan=3, sticky='w', pady=5)
        TooltipHelper(quality_cb, "Analyze image quality, resolution, sharpness")

        # Video scene detection
        self.video_scene_var = tk.BooleanVar(value=False)
        video_cb = ttk.Checkbutton(self, text="Video Scene Detection & Key Frames",
                                  variable=self.video_scene_var)
        video_cb.grid(row=7, column=0, columnspan=3, sticky='w', pady=5)
        TooltipHelper(video_cb, "Detect scene changes and extract key moments from videos")

        # Audio transcription
        self.audio_transcription_var = tk.BooleanVar(value=False)
        audio_cb = ttk.Checkbutton(self, text="Audio Transcription & Analysis",
                                  variable=self.audio_transcription_var)
        audio_cb.grid(row=8, column=0, columnspan=3, sticky='w', pady=5)
        TooltipHelper(audio_cb, "Transcribe audio and detect content type")

    def toggle_nsfw_options(self):
        """Enable/disable NSFW-related options."""
        state = 'normal' if self.nsfw_detection_var.get() else 'disabled'
        self.confidence_scale.config(state=state)

    def update_confidence_label(self, *args):
        """Update confidence threshold label."""
        self.confidence_label.config(text=f"{self.confidence_var.get():.2f}")

    def get_config(self) -> Dict[str, Any]:
        """Extract configuration from widgets."""
        return {
            'nsfw_detection': self.nsfw_detection_var.get(),
            'confidence_threshold': self.confidence_var.get(),
            'object_detection': self.object_detection_var.get(),
            'color_analysis': self.color_analysis_var.get(),
            'face_detection': self.face_detection_var.get(),
            'scene_classification': self.scene_classification_var.get(),
            'quality_metrics': self.quality_metrics_var.get(),
            'video_scene_detection': self.video_scene_var.get(),
            'audio_transcription': self.audio_transcription_var.get()
        }

    def set_config(self, config: Dict[str, Any]):
        """Apply configuration to widgets."""
        self.nsfw_detection_var.set(config.get('nsfw_detection', True))
        self.confidence_var.set(config.get('confidence_threshold', 0.6))
        self.object_detection_var.set(config.get('object_detection', False))
        self.color_analysis_var.set(config.get('color_analysis', False))
        self.face_detection_var.set(config.get('face_detection', False))
        self.scene_classification_var.set(config.get('scene_classification', False))
        self.quality_metrics_var.set(config.get('quality_metrics', False))
        self.video_scene_var.set(config.get('video_scene_detection', False))
        self.audio_transcription_var.set(config.get('audio_transcription', False))
        self.toggle_nsfw_options()


class OrganizationFrame(ttk.LabelFrame):
    """Frame for file organization options."""

    def __init__(self, parent):
        super().__init__(parent, text="📁 File Organization", padding=10)
        self.create_widgets()

    def create_widgets(self):
        # Organization mode
        ttk.Label(self, text="Organization Mode:").grid(row=0, column=0, sticky='w', pady=5)
        self.mode_var = tk.StringVar(value="skip")
        mode_frame = ttk.Frame(self)
        mode_frame.grid(row=0, column=1, columnspan=2, sticky='w', padx=5, pady=5)

        ttk.Radiobutton(mode_frame, text="Skip (Scan only)", variable=self.mode_var,
                       value="skip").pack(side='left', padx=5)
        ttk.Radiobutton(mode_frame, text="Copy files", variable=self.mode_var,
                       value="copy").pack(side='left', padx=5)
        ttk.Radiobutton(mode_frame, text="Move files", variable=self.mode_var,
                       value="move").pack(side='left', padx=5)

        # Organization structure
        ttk.Label(self, text="Organize By:").grid(row=1, column=0, sticky='w', pady=5)
        self.organize_by_var = tk.StringVar(value="classification")
        org_combo = ttk.Combobox(self, textvariable=self.organize_by_var,
                                values=['classification', 'type', 'date', 'size',
                                       'color', 'tags', 'quality', 'scene'],
                                state='readonly', width=20)
        org_combo.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        TooltipHelper(org_combo, "Primary organization method")

        # Date hierarchy
        self.date_hierarchy_var = tk.BooleanVar(value=False)
        date_cb = ttk.Checkbutton(self, text="Use Date Hierarchy (Year/Month/Day)",
                                 variable=self.date_hierarchy_var)
        date_cb.grid(row=2, column=1, columnspan=2, sticky='w', pady=5)
        TooltipHelper(date_cb, "Create folders like 2024/01/15/ based on file dates")

        # Keep structure
        self.keep_structure_var = tk.BooleanVar(value=False)
        struct_cb = ttk.Checkbutton(self, text="Preserve Original Directory Structure",
                                   variable=self.keep_structure_var)
        struct_cb.grid(row=3, column=1, columnspan=2, sticky='w', pady=5)
        TooltipHelper(struct_cb, "Maintain folder hierarchy in organized output")

        # Output directory
        ttk.Label(self, text="Output Directory:").grid(row=4, column=0, sticky='w', pady=5)
        self.output_dir_var = tk.StringVar(value=str(Path.home() / "Desktop" / "Media_Scan_Results"))
        output_entry = ttk.Entry(self, textvariable=self.output_dir_var, width=40)
        output_entry.grid(row=4, column=1, padx=5, pady=5)

        output_btn = ttk.Button(self, text="Browse...", command=self.browse_output_dir)
        output_btn.grid(row=4, column=2, padx=5)

        # Naming template
        ttk.Label(self, text="File Naming:").grid(row=5, column=0, sticky='w', pady=5)
        self.naming_template_var = tk.StringVar(value="{original}")
        naming_combo = ttk.Combobox(self, textvariable=self.naming_template_var,
                                   values=['{original}',
                                          '{date}_{original}',
                                          '{type}_{date}_{counter}',
                                          '{date}_{classification}_{counter}'],
                                   width=30)
        naming_combo.grid(row=5, column=1, columnspan=2, sticky='w', padx=5, pady=5)
        TooltipHelper(naming_combo, "File naming pattern for organized files")

    def browse_output_dir(self):
        """Open folder browser for output directory."""
        folder = filedialog.askdirectory(initialdir=self.output_dir_var.get(),
                                        title="Select output directory")
        if folder:
            self.output_dir_var.set(folder)

    def get_config(self) -> Dict[str, Any]:
        """Extract configuration from widgets."""
        return {
            'mode': self.mode_var.get(),
            'organize_by': self.organize_by_var.get(),
            'date_hierarchy': self.date_hierarchy_var.get(),
            'keep_structure': self.keep_structure_var.get(),
            'output_dir': self.output_dir_var.get(),
            'naming_template': self.naming_template_var.get()
        }

    def set_config(self, config: Dict[str, Any]):
        """Apply configuration to widgets."""
        self.mode_var.set(config.get('mode', 'skip'))
        self.organize_by_var.set(config.get('organize_by', 'classification'))
        self.date_hierarchy_var.set(config.get('date_hierarchy', False))
        self.keep_structure_var.set(config.get('keep_structure', False))
        self.output_dir_var.set(config.get('output_dir', str(Path.home() / "Desktop" / "Media_Scan_Results")))
        self.naming_template_var.set(config.get('naming_template', '{original}'))


class PerformanceFrame(ttk.LabelFrame):
    """Frame for performance and advanced options."""

    def __init__(self, parent):
        super().__init__(parent, text="⚡ Performance & Advanced", padding=10)
        self.create_widgets()

    def create_widgets(self):
        # Worker threads
        ttk.Label(self, text="Worker Threads:").grid(row=0, column=0, sticky='w', pady=5)
        self.workers_var = tk.IntVar(value=4)
        workers_spin = ttk.Spinbox(self, from_=1, to=16, textvariable=self.workers_var, width=10)
        workers_spin.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        TooltipHelper(workers_spin, "Number of parallel processing threads (2-8 recommended)")

        # Batch size
        ttk.Label(self, text="Batch Size:").grid(row=1, column=0, sticky='w', pady=5)
        self.batch_size_var = tk.IntVar(value=1000)
        batch_spin = ttk.Spinbox(self, from_=100, to=5000, increment=100,
                                textvariable=self.batch_size_var, width=10)
        batch_spin.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        TooltipHelper(batch_spin, "Files to process before reporting progress")

        # Priority mode
        ttk.Label(self, text="Priority:").grid(row=2, column=0, sticky='w', pady=5)
        self.priority_var = tk.StringVar(value="balanced")
        priority_combo = ttk.Combobox(self, textvariable=self.priority_var,
                                     values=['fast', 'balanced', 'thorough'],
                                     state='readonly', width=15)
        priority_combo.grid(row=2, column=1, sticky='w', padx=5, pady=5)
        TooltipHelper(priority_combo, "Fast=speed, Balanced=quality/speed, Thorough=maximum accuracy")

        # Cache results
        self.cache_results_var = tk.BooleanVar(value=False)
        cache_cb = ttk.Checkbutton(self, text="Cache analysis results",
                                  variable=self.cache_results_var)
        cache_cb.grid(row=3, column=1, sticky='w', pady=5)
        TooltipHelper(cache_cb, "Cache results to speed up re-scans of same files")

        # Duplicate detection
        self.detect_duplicates_var = tk.BooleanVar(value=False)
        dup_cb = ttk.Checkbutton(self, text="Detect duplicate files",
                                variable=self.detect_duplicates_var)
        dup_cb.grid(row=4, column=1, sticky='w', pady=5)
        TooltipHelper(dup_cb, "Find duplicate files using file hashing")

        # Video size limit
        ttk.Label(self, text="Video Size Limit:").grid(row=5, column=0, sticky='w', pady=5)
        self.video_limit_var = tk.StringVar(value="500MB")
        video_entry = ttk.Entry(self, textvariable=self.video_limit_var, width=15)
        video_entry.grid(row=5, column=1, sticky='w', padx=5, pady=5)
        TooltipHelper(video_entry, "Maximum video file size to process (e.g., 500MB, 1GB)")

    def get_config(self) -> Dict[str, Any]:
        """Extract configuration from widgets."""
        return {
            'workers': self.workers_var.get(),
            'batch_size': self.batch_size_var.get(),
            'priority': self.priority_var.get(),
            'cache_results': self.cache_results_var.get(),
            'detect_duplicates': self.detect_duplicates_var.get(),
            'video_size_limit': self.video_limit_var.get()
        }

    def set_config(self, config: Dict[str, Any]):
        """Apply configuration to widgets."""
        self.workers_var.set(config.get('workers', 4))
        self.batch_size_var.set(config.get('batch_size', 1000))
        self.priority_var.set(config.get('priority', 'balanced'))
        self.cache_results_var.set(config.get('cache_results', False))
        self.detect_duplicates_var.set(config.get('detect_duplicates', False))
        self.video_limit_var.set(config.get('video_size_limit', '500MB'))


class MediaScannerGUI:
    """Main GUI application for Enhanced Media Scanner."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Enhanced Media Scanner v3.0 ULTRA BUFF Edition")
        self.root.geometry("950x850")

        # Initialize profile manager
        self.profile_manager = ConfigurationProfile()

        # Apply modern theme
        self.setup_theme()

        # Create main layout
        self.create_widgets()

        # Scan thread
        self.scan_thread = None
        self.scanning = False

    def setup_theme(self):
        """Apply modern ttk theme and styling."""
        style = ttk.Style()

        # Use modern theme if available
        available_themes = style.theme_names()
        if 'vista' in available_themes:
            style.theme_use('vista')
        elif 'clam' in available_themes:
            style.theme_use('clam')

        # Custom color scheme
        style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'))
        style.configure('Subtitle.TLabel', font=('Segoe UI', 10))
        style.configure('TButton', padding=5)
        style.configure('Action.TButton', padding=10, font=('Segoe UI', 10, 'bold'))

    def create_widgets(self):
        """Create main GUI layout."""
        # Header
        header_frame = ttk.Frame(self.root, padding=10)
        header_frame.pack(fill='x')

        ttk.Label(header_frame, text="🚀 Enhanced Media Scanner",
                 style='Title.TLabel').pack()
        ttk.Label(header_frame, text="AI-Powered Media Detection & Organization System",
                 style='Subtitle.TLabel').pack()

        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)

        # Tab 1: Basic Configuration
        basic_tab = ttk.Frame(self.notebook)
        self.notebook.add(basic_tab, text="Basic Settings")
        self.create_basic_tab(basic_tab)

        # Tab 2: AI Features
        ai_tab = ttk.Frame(self.notebook)
        self.notebook.add(ai_tab, text="AI Features")
        self.create_ai_tab(ai_tab)

        # Tab 3: Organization
        org_tab = ttk.Frame(self.notebook)
        self.notebook.add(org_tab, text="Organization")
        self.create_organization_tab(org_tab)

        # Tab 4: Advanced
        advanced_tab = ttk.Frame(self.notebook)
        self.notebook.add(advanced_tab, text="Advanced")
        self.create_advanced_tab(advanced_tab)

        # Bottom control panel
        self.create_control_panel()

    def create_basic_tab(self, parent):
        """Create basic settings tab."""
        container = ttk.Frame(parent, padding=10)
        container.pack(fill='both', expand=True)

        # Scan configuration
        self.scan_config_frame = ScanConfigFrame(container)
        self.scan_config_frame.pack(fill='x', pady=5)

        # File filtering
        self.file_filter_frame = FileFilterFrame(container)
        self.file_filter_frame.pack(fill='x', pady=5)

    def create_ai_tab(self, parent):
        """Create AI features tab."""
        container = ttk.Frame(parent, padding=10)
        container.pack(fill='both', expand=True)

        self.ai_features_frame = AIFeaturesFrame(container)
        self.ai_features_frame.pack(fill='both', expand=True)

        # Info label
        info_frame = ttk.Frame(container)
        info_frame.pack(fill='x', pady=10)

        info_text = """
💡 Note: AI features require additional dependencies:
   • NSFW Detection: nudenet (pip install nudenet)
   • Object Detection: torch, ultralytics (pip install torch ultralytics)
   • Face Detection: face_recognition (pip install face-recognition)
   • Color Analysis: scikit-learn, colorthief (pip install scikit-learn colorthief)
   • Audio Transcription: whisper (pip install openai-whisper)
        """
        ttk.Label(info_frame, text=info_text, justify='left',
                 foreground='#666').pack(anchor='w')

    def create_organization_tab(self, parent):
        """Create organization tab."""
        container = ttk.Frame(parent, padding=10)
        container.pack(fill='both', expand=True)

        self.organization_frame = OrganizationFrame(container)
        self.organization_frame.pack(fill='both', expand=True)

    def create_advanced_tab(self, parent):
        """Create advanced settings tab."""
        container = ttk.Frame(parent, padding=10)
        container.pack(fill='both', expand=True)

        self.performance_frame = PerformanceFrame(container)
        self.performance_frame.pack(fill='x', pady=5)

        # Exclusion patterns
        exclude_frame = ttk.LabelFrame(container, text="📋 Exclusion Patterns", padding=10)
        exclude_frame.pack(fill='both', expand=True, pady=5)

        ttk.Label(exclude_frame, text="Additional directories to exclude (comma-separated):").pack(anchor='w')
        self.exclude_dirs_var = tk.StringVar(value="")
        exclude_entry = ttk.Entry(exclude_frame, textvariable=self.exclude_dirs_var, width=70)
        exclude_entry.pack(fill='x', pady=5)
        TooltipHelper(exclude_entry, "Add custom directory patterns to exclude")

    def create_control_panel(self):
        """Create bottom control panel with action buttons."""
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill='x', side='bottom')

        # Profile management
        profile_frame = ttk.LabelFrame(control_frame, text="Configuration Profiles", padding=5)
        profile_frame.pack(side='left', fill='x', expand=True, padx=5)

        profile_btn_frame = ttk.Frame(profile_frame)
        profile_btn_frame.pack(fill='x')

        ttk.Button(profile_btn_frame, text="Save Profile",
                  command=self.save_profile).pack(side='left', padx=2)
        ttk.Button(profile_btn_frame, text="Load Profile",
                  command=self.load_profile).pack(side='left', padx=2)
        ttk.Button(profile_btn_frame, text="Delete Profile",
                  command=self.delete_profile).pack(side='left', padx=2)

        # Action buttons
        action_frame = ttk.Frame(control_frame)
        action_frame.pack(side='right', padx=5)

        self.start_btn = ttk.Button(action_frame, text="▶ Start Scan",
                                    style='Action.TButton',
                                    command=self.start_scan)
        self.start_btn.pack(side='left', padx=5)

        self.stop_btn = ttk.Button(action_frame, text="⏹ Stop",
                                   command=self.stop_scan,
                                   state='disabled')
        self.stop_btn.pack(side='left', padx=5)

        ttk.Button(action_frame, text="❌ Exit",
                  command=self.root.quit).pack(side='left', padx=5)

        # Status bar
        self.status_var = tk.StringVar(value="Ready to scan")
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                              relief='sunken', anchor='w')
        status_bar.pack(fill='x', side='bottom')

    def get_full_config(self) -> Dict[str, Any]:
        """Collect configuration from all frames."""
        config = {}
        config.update(self.scan_config_frame.get_config())
        config.update(self.file_filter_frame.get_config())
        config.update(self.ai_features_frame.get_config())
        config.update(self.organization_frame.get_config())
        config.update(self.performance_frame.get_config())
        config['exclude_dirs'] = self.exclude_dirs_var.get().strip() or None

        return config

    def set_full_config(self, config: Dict[str, Any]):
        """Apply configuration to all frames."""
        self.scan_config_frame.set_config(config)
        self.file_filter_frame.set_config(config)
        self.ai_features_frame.set_config(config)
        self.organization_frame.set_config(config)
        self.performance_frame.set_config(config)
        self.exclude_dirs_var.set(config.get('exclude_dirs', '') or '')

    def save_profile(self):
        """Save current configuration as a profile."""
        profile_name = tk.simpledialog.askstring("Save Profile",
                                                 "Enter profile name:",
                                                 parent=self.root)
        if profile_name:
            config = self.get_full_config()
            if self.profile_manager.save_profile(profile_name, config):
                messagebox.showinfo("Success", f"Profile '{profile_name}' saved successfully!")
            else:
                messagebox.showerror("Error", "Failed to save profile")

    def load_profile(self):
        """Load a saved configuration profile."""
        profiles = self.profile_manager.list_profiles()

        if not profiles:
            messagebox.showinfo("No Profiles", "No saved profiles found")
            return

        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Load Profile")
        dialog.geometry("300x400")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Select a profile to load:",
                 font=('Segoe UI', 10, 'bold')).pack(pady=10)

        listbox = tk.Listbox(dialog, font=('Segoe UI', 10))
        listbox.pack(fill='both', expand=True, padx=10, pady=5)

        for profile in sorted(profiles):
            listbox.insert('end', profile)

        def on_load():
            selection = listbox.curselection()
            if selection:
                profile_name = listbox.get(selection[0])
                config = self.profile_manager.load_profile(profile_name)
                if config:
                    self.set_full_config(config)
                    messagebox.showinfo("Success", f"Profile '{profile_name}' loaded!")
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Failed to load profile")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(btn_frame, text="Load", command=on_load).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side='right', padx=5)

    def delete_profile(self):
        """Delete a saved profile."""
        profiles = self.profile_manager.list_profiles()

        if not profiles:
            messagebox.showinfo("No Profiles", "No saved profiles found")
            return

        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Delete Profile")
        dialog.geometry("300x400")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Select a profile to delete:",
                 font=('Segoe UI', 10, 'bold')).pack(pady=10)

        listbox = tk.Listbox(dialog, font=('Segoe UI', 10))
        listbox.pack(fill='both', expand=True, padx=10, pady=5)

        for profile in sorted(profiles):
            listbox.insert('end', profile)

        def on_delete():
            selection = listbox.curselection()
            if selection:
                profile_name = listbox.get(selection[0])
                if messagebox.askyesno("Confirm Delete",
                                      f"Delete profile '{profile_name}'?"):
                    if self.profile_manager.delete_profile(profile_name):
                        messagebox.showinfo("Success", f"Profile '{profile_name}' deleted")
                        dialog.destroy()
                    else:
                        messagebox.showerror("Error", "Failed to delete profile")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(btn_frame, text="Delete", command=on_delete).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side='right', padx=5)

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, str]:
        """Validate configuration before starting scan."""
        # Check scan path exists
        scan_path = Path(config['scan_path'])
        if not scan_path.exists():
            return False, f"Scan path does not exist: {scan_path}"

        if not scan_path.is_dir():
            return False, f"Scan path is not a directory: {scan_path}"

        # Validate size formats
        for size_key in ['min_size', 'max_size', 'video_size_limit']:
            size_str = config.get(size_key)
            if size_str and not self.parse_size(size_str):
                return False, f"Invalid size format: {size_str}"

        # Validate dates
        for date_key in ['modified_after', 'modified_before']:
            date_str = config.get(date_key)
            if date_str:
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    return False, f"Invalid date format (use YYYY-MM-DD): {date_str}"

        return True, "Configuration valid"

    def parse_size(self, size_str: str) -> Optional[int]:
        """Parse size string like '100MB' to bytes."""
        if not size_str:
            return None

        size_str = size_str.upper().strip()

        units = {
            'B': 1,
            'KB': 1024,
            'MB': 1024**2,
            'GB': 1024**3,
            'TB': 1024**4
        }

        for unit, multiplier in units.items():
            if size_str.endswith(unit):
                try:
                    value = float(size_str[:-len(unit)])
                    return int(value * multiplier)
                except ValueError:
                    return None

        # Try parsing as plain number (bytes)
        try:
            return int(size_str)
        except ValueError:
            return None

    def start_scan(self):
        """Start the scanning process in a background thread."""
        # Get configuration
        config = self.get_full_config()

        # Validate configuration
        valid, message = self.validate_config(config)
        if not valid:
            messagebox.showerror("Configuration Error", message)
            return

        # Confirm with user
        if not messagebox.askyesno("Confirm Scan",
                                   f"Start scanning: {config['scan_path']}?\n\n" +
                                   f"This may take a while depending on the number of files."):
            return

        # Disable start button, enable stop button
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.scanning = True

        # Update status
        self.status_var.set("Initializing scan...")

        # Start scan in background thread
        self.scan_thread = threading.Thread(target=self.run_scan, args=(config,), daemon=True)
        self.scan_thread.start()

    def stop_scan(self):
        """Stop the scanning process."""
        if messagebox.askyesno("Confirm Stop", "Are you sure you want to stop the scan?"):
            self.scanning = False
            self.status_var.set("Stopping scan...")

    def run_scan(self, config: Dict[str, Any]):
        """Execute scan in background thread."""
        try:
            # Import ultra scanner
            from media_scanner_ultra import create_scanner_from_config

            # Update status
            self.root.after(0, lambda: self.status_var.set("Initializing AI models..."))

            # Create scanner from configuration
            scanner = create_scanner_from_config(config)

            # Update status
            self.root.after(0, lambda: self.status_var.set("Scanning in progress..."))

            # Run scan
            scanner.scan_drive(drive=config['scan_path'],
                             max_files=config.get('max_files'))

            # Update status
            self.root.after(0, lambda: self.status_var.set("Generating reports..."))

            # Generate reports
            output_dir = Path(config['output_dir'])
            report_files = scanner.generate_report(output_dir)

            # Organize files if requested (using advanced organization)
            if config['mode'] != 'skip':
                self.root.after(0, lambda: self.status_var.set("Organizing files..."))
                organize_base = output_dir / "Organized_Media"

                # Use advanced organization with AI features
                org_config = {
                    'mode': config['mode'],
                    'organize_by': config.get('organize_by', 'classification'),
                    'date_hierarchy': config.get('date_hierarchy', False),
                    'keep_structure': config.get('keep_structure', False),
                    'naming_template': config.get('naming_template', '{original}')
                }

                scanner.organize_files_advanced(organize_base, org_config)

            # Update status
            self.root.after(0, lambda: self.status_var.set(f"Scan complete! Results in: {output_dir}"))

            # Show completion message
            report_count = len(report_files)
            msg = f"Scan completed successfully!\n\n"
            msg += f"Results saved to:\n{output_dir}\n\n"
            msg += f"Generated {report_count} report file(s):\n"
            for report in report_files:
                msg += f"  • {report.name}\n"

            self.root.after(0, lambda: messagebox.showinfo("Scan Complete", msg))

        except ImportError as e:
            error_msg = f"Missing dependency: {str(e)}\n\nPlease install required packages:\npip install -r requirements.txt"
            self.root.after(0, lambda: self.status_var.set("Error: Missing dependencies"))
            self.root.after(0, lambda: messagebox.showerror("Import Error", error_msg))

        except Exception as e:
            error_msg = f"Error during scan: {str(e)}"
            self.root.after(0, lambda: self.status_var.set(error_msg))
            self.root.after(0, lambda: messagebox.showerror("Scan Error", error_msg))

        finally:
            # Re-enable buttons
            self.root.after(0, lambda: self.start_btn.config(state='normal'))
            self.root.after(0, lambda: self.stop_btn.config(state='disabled'))
            self.scanning = False

    def run(self):
        """Start the GUI main loop."""
        self.root.mainloop()


def main():
    """Entry point for GUI application."""
    app = MediaScannerGUI()
    app.run()


if __name__ == "__main__":
    main()
