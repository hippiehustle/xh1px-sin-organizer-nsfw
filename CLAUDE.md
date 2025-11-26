# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Enhanced Media Scanner v2.0** - An AI-powered NSFW media detection and organization tool for Windows. The application uses NudeNet (deep learning visual analysis) combined with filename-based classification to detect and organize media files.

- **Status:** Production-ready (BUFF enhanced v2)
- **Language:** Python 3.13 (required)
- **Main Entry Point:** `media_scanner.py` (~916 lines)
- **Deployment:** Windows 10/11 batch scripts for one-click setup and execution

## Architecture & Core Components

### Main Application Structure

The `media_scanner.py` module is organized around these key classes:

1. **`DetectionResult` (Dataclass)**
   - Encapsulates detection metadata: confidence scores, NSFW labels, detection method, processing time
   - Immutable with `to_dict()` method for JSON serialization
   - Prevents common bugs with mutable defaults via dataclass field factories

2. **`FileInfo` (Dataclass)**
   - Stores complete file metadata: path, size, hash, extension, modification date, detection results
   - All fields are type-hinted and JSON-serializable

3. **`RateLimiter` (Token Bucket Implementation)**
   - Prevents throttling during parallel video frame processing
   - Configured for 5 calls/second (adjustable via constructor)
   - Critical for reliable batch processing without API rate limit errors

4. **`EnhancedMediaScanner` (Main Processing Engine)**
   - Orchestrates the entire detection pipeline
   - Parallel file processing via `ThreadPoolExecutor` (default 4 workers)
   - Two detection methods:
     - **Visual Analysis:** Uses NudeNet deep learning model for image/video analysis
     - **Filename Analysis:** Fallback keyword matching when visual analysis unavailable
   - Video support: Extracts frames at 30-second intervals (max 10 frames per video)
   - Generates comprehensive JSON reports with metrics and file organization

### Critical Implementation Details

**Configuration Constants** (in `EnhancedMediaScanner` class):
- `CONFIDENCE_THRESHOLD = 0.6` - Minimum confidence score for NSFW classification
- `VIDEO_SIZE_LIMIT = 500MB` - Maximum processable video size
- `MAX_PATH_LENGTH = 260` - Windows MAX_PATH limit (enforced, not just a warning)
- `DETECTION_TIMEOUT = 30s` - Per-file processing timeout
- `HASH_READ_SIZE = 8192 bytes` - Chunk size for file hashing

**File Type Sets** (frozensets for O(1) lookups):
- `image_extensions` - jpg, png, gif, webp, heic, svg, etc.
- `video_extensions` - mp4, mkv, mov, avi, flv, webm, etc.
- `audio_extensions` - mp3, wav, flac, aac, ogg, etc.

**System Exclusions** (case-insensitive patterns):
- Windows system directories (Windows, Program Files, ProgramData, $Recycle.Bin)
- Development directories (.git, __pycache__, node_modules, venv)
- Cache/temp directories (AppData\Local\Temp, cache, thumbnails)
- This prevents scanning protected OS files and speeds up scans significantly

**NSFW Keywords** (lowercase keyword matching):
- 50+ keywords including: nude, xxx, porn, hentai, onlyfans, etc.
- Used as fallback when NudeNet unavailable
- Keywords are split intelligently (not just substring matching)

### Windows-Specific Handling

- UTF-8 console encoding fix (line 27-32) for proper Unicode output on Windows
- Path length validation before processing (Windows 260-char limit)
- PID-based temp file naming to prevent collisions in shared temp directories
- Platform detection: `platform.system() == 'Windows'` for conditional logic

## Common Development Tasks

### Running the Scanner

**Normal execution** (via batch file):
```powershell
# Users run this
run_scanner.bat
```

**Direct Python execution** (for testing/debugging):
```powershell
py -3.13 media_scanner.py
```

**With custom parameters**:
```powershell
py -3.13 media_scanner.py --scan-path "C:\Users\YourName\Pictures" --mode move
```

### Running Tests

```powershell
cd tests
py -3.13 test_scanner.py
```

**Current test results:** 18 tests, 16 passing (88.9% success rate). 2 minor failures related to temp directory scanning (non-critical for production).

**Test coverage includes:**
- Unit tests: DetectionResult, FileInfo, RateLimiter, path exclusion logic
- Integration tests: Full scan workflows, JSON report generation
- Edge cases: Unicode handling, Windows MAX_PATH violations, missing dependencies

### Installation & Dependencies

**One-click setup**:
```powershell
setup.bat  # Validates Python 3.13, installs dependencies
```

**Manual installation**:
```powershell
py -3.13 -m pip install pillow numpy nudenet opencv-python
```

**Dependency rationale:**
- `pillow` - Image reading/manipulation
- `numpy` - Numerical operations
- `nudenet` - AI visual analysis (optional but recommended)
- `opencv-python` - Video frame extraction (optional but needed for video support)

**Important:** Python 3.13 is required, not 3.14. Python 3.14 lacks pre-built wheels for scikit-image (NudeNet dependency), requiring source compilation that can take 5-10 minutes.

## Key Design Patterns

### Graceful Degradation

When NudeNet is unavailable (missing dependency):
1. Scanner logs a warning and switches to filename-only detection
2. All features continue working, just with less accuracy
3. No hard failure - design is defensive

### Error Handling Hierarchy

- Try-catch blocks with specific exception types (not bare exceptions)
- Comprehensive logging at DEBUG, INFO, WARNING, ERROR levels
- Detailed traceback in error logs for debugging
- Temporary file cleanup in `finally` blocks (resource safety)

### Performance Optimization

- **Threading:** `ThreadPoolExecutor` for parallel file processing (default 4 workers)
- **Rate Limiting:** Token bucket to prevent API throttling during batch processing
- **Path Caching:** Frozensets for directory exclusions and file extensions (O(1) lookup)
- **Progress Throttling:** Maximum 1 progress update per second (prevents console flooding)
- **Batch Processing:** Organizes 1000 files per batch when copying/moving

### Data Safety

- Read-only by default (scan without modifying files)
- Copy mode preserves originals, creates isolated folder structure
- Atomic file operations with collision handling (prevents overwriting)
- Safe temp directory creation with fallback paths

## Important Files & Modules

| File | Purpose |
|------|---------|
| `media_scanner.py` | Main application (916 lines) |
| `setup.bat` | One-click dependency installer |
| `run_scanner.bat` | One-click launcher script |
| `tests/test_scanner.py` | Comprehensive test suite |
| `docs/README.md` | Detailed user documentation |
| `docs/TROUBLESHOOTING.md` | Common issues and solutions |
| `requirements.txt` | Python dependencies list |

## Testing & Debugging Tips

- Use `CONFIDENCE_THRESHOLD` to adjust sensitivity (lower = more detections)
- Enable debug logging to trace detection pipeline
- Check `processing_time` in JSON reports to identify bottlenecks
- For video issues, verify OpenCV is installed and frame extraction works
- For Unicode issues on Windows, ensure UTF-8 console encoding is applied (already handled)

## Notes for Future Development

- The scanner is production-ready with comprehensive error handling
- Performance metrics are tracked per file (hashing time, visual analysis time)
- Skipped files are tracked (files over 500MB, paths exceeding 260 chars)
- All configuration is immutable (no magic strings scattered throughout code)
- Type hints are comprehensive - use for IDE autocompletion and validation
