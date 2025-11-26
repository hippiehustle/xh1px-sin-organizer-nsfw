# Enhanced Media Scanner v2.0 BUFF

Professional-grade AI-powered NSFW media detection and organization tool for Windows.

## Quick Start

### Method 1: One-Click Setup (Easiest)
```
1. Double-click: setup.bat          (one-time, installs dependencies)
2. Double-click: run_scanner.bat    (starts interactive menu)
```

### Method 2: Command Line (Advanced)
```powershell
# Scan C: drive and copy files
py -3.13 media_scanner.py --scan-path C: --mode copy

# Scan specific folder
py -3.13 media_scanner.py --scan-path D:\Pictures

# See all options
py -3.13 media_scanner.py --help
```

Results save to: `Desktop/Media_Scan_Results/`

---

## System Requirements

| Requirement | Details |
|---|---|
| **OS** | Windows 10/11 (64-bit) |
| **Python** | Python 3.13 (required, not 3.14) |
| **RAM** | 4GB minimum, 8GB+ recommended |
| **Disk** | 500MB for dependencies + space for results |

### Why Python 3.13 (not 3.14)?

Python 3.14 is too new - NudeNet and scikit-image don't have pre-built wheels yet. Python 3.13 works perfectly and installs in 2 minutes.

**Check your Python version:**
```powershell
py -0
```

**Install Python 3.13:** [python.org/downloads](https://www.python.org/downloads)

---

## Features

### Detection Methods
✅ **AI Visual Analysis** - Deep learning (NudeNet) for accurate detection
✅ **Filename Detection** - 70+ keyword indicators for content classification
✅ **Video Support** - Intelligent frame extraction (30-second intervals)
✅ **Multi-Format** - Images, videos, and audio files

### Organization & Reporting
✅ **Smart Organization** - Sort files into SFW/NSFW/Uncertain categories
✅ **JSON Reports** - Detailed analysis with confidence scores
✅ **Performance Metrics** - Processing time, file statistics, analysis breakdown
✅ **Optional File Operations** - Copy or move files to organized folders

### Safety & Reliability
✅ **100% Local** - No cloud, no internet required
✅ **Read-Only Default** - Scan without modifying original files
✅ **Graceful Degradation** - Works even if NudeNet isn't available
✅ **Comprehensive Logging** - Full error tracking and debug information

---

## What It Does

```
INPUT  → Scan C: drive or specific folder
         ↓
DETECT → AI visual analysis + filename keywords
         ↓
CLASSIFY → SFW (safe) / NSFW (explicit) / Uncertain
         ↓
OUTPUT → JSON report + optional organized folders
```

---

## Command-Line Options

```
usage: media_scanner.py [options]

Scanning:
  --scan-path PATH          Folder to scan (default: C:\)
  --output-dir PATH         Results directory (default: Desktop/Media_Scan_Results)
  --max-files N             Limit scan to N files (default: unlimited)

Analysis:
  --no-visual               Disable AI analysis (filename-only mode)
  --confidence SCORE        NSFW threshold 0.0-1.0 (default: 0.6)

File Operations:
  --mode {copy,move,skip}   Organize files (default: skip)

Performance:
  --workers N               Parallel workers (default: 4)

Interaction:
  --no-confirm              Skip confirmation prompts

Examples:
  py -3.13 media_scanner.py
  py -3.13 media_scanner.py --scan-path D:\Downloads --mode copy
  py -3.13 media_scanner.py --scan-path C: --max-files 5000 --no-visual
  py -3.13 media_scanner.py --confidence 0.7 --workers 8
```

---

## Installation

### Automatic (Recommended)
```
Double-click setup.bat
```

### Manual
```powershell
# Install Python 3.13 first, then:
py -3.13 -m pip install pillow numpy opencv-python nudenet
```

---

## Usage Examples

### Standard Scan (Interactive)
```powershell
py -3.13 media_scanner.py
# Follow the prompts
```

### Fast Scan with Copy
```powershell
py -3.13 media_scanner.py --scan-path D:\Pictures --mode copy --no-confirm
```

### High Sensitivity Detection
```powershell
py -3.13 media_scanner.py --scan-path C: --confidence 0.5 --no-confirm
```

### Filename Analysis Only
```powershell
py -3.13 media_scanner.py --no-visual --scan-path C: --no-confirm
```

### Limited Scan (Testing)
```powershell
py -3.13 media_scanner.py --max-files 100 --no-confirm
```

---

## Output

### Files Created
```
Desktop/Media_Scan_Results/
├── enhanced_scan_report_TIMESTAMP.json     # Detailed analysis
├── enhanced_scan_summary_TIMESTAMP.txt     # Human-readable summary
├── logs/scan_TIMESTAMP.log                 # Debug information
└── Organized_Media/                        # (optional, if using --mode)
    ├── images/
    │   ├── sfw/      # Safe images
    │   ├── nsfw/     # Explicit images
    │   └── uncertain/ # Unclear classification
    ├── videos/       # Same structure
    └── audio/        # Same structure
```

### Report Contents
- File counts and classifications (SFW/NSFW/Uncertain)
- Confidence scores for detected content
- Processing times and performance metrics
- Error tracking and skipped files
- Detailed analysis breakdown by media type

---

## Safety & Privacy

| Aspect | Details |
|---|---|
| **Data Processing** | 100% local (no uploads, no cloud) |
| **File Modification** | Read-only by default |
| **Copies/Moves** | Optional, preserves originals with copy mode |
| **Logging** | Local logs with full debug info |
| **Reversibility** | Use copy mode for safer organization |

---

## Troubleshooting

| Error | Solution |
|---|---|
| "Python 3.13 not found" | Install from [python.org](https://python.org) |
| "NudeNet installation failed" | Run `setup.bat` again, or check internet connection |
| "Scanner uses filename-only mode" | Install NudeNet: `py -3.13 -m pip install nudenet` |
| "OpenCV not installed" | For video support: `py -3.13 -m pip install opencv-python` |
| "Access denied" | Run as Administrator or skip protected system folders |

**More help:** See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## Documentation

- **[Full Technical Guide](docs/README.md)** - Complete architecture and features
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[BUFF Report](docs/BUFF_REPORT.md)** - Version 2.0 improvements

---

## Project Structure

```
media_organizer/
├── media_scanner.py           # Main application (900+ lines)
├── setup.bat                  # Dependency installer (enhanced)
├── run_scanner.bat            # Smart launcher with menu
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── CLAUDE.md                  # Architecture documentation
├── docs/
│   ├── README.md              # Full documentation
│   ├── TROUBLESHOOTING.md     # Common issues
│   └── BUFF_REPORT.md         # v2.0 improvements
├── tests/
│   └── test_scanner.py        # Test suite
└── legacy/                    # Previous versions
```

---

## Version History

| Version | Date | Status | Key Features |
|---|---|---|---|
| 2.0 BUFF | 2024 | ✅ Latest | CLI args, enhanced keywords, smart launcher |
| 2.0 | 2024 | ✅ Stable | AI visual analysis, video support |
| 1.x | 2023 | 🔄 Legacy | Initial release |

---

## Performance

Typical scan times on a modern machine:
- **1,000 files**: 5-10 minutes (with AI analysis)
- **5,000 files**: 25-50 minutes
- **10,000+ files**: Use `--max-files` or split scans

Factors affecting speed:
- File sizes (larger files take longer)
- File types (videos slower than images)
- System specifications (more RAM/CPU = faster)
- NudeNet availability (AI analysis takes ~0.5-1s per image)

---

**Version:** 2.0 BUFF (Enhanced)
**Status:** ✅ Production Ready
**Python:** 3.13 Required
**License:** Personal Use
**Updated:** 2024
