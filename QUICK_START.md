# Enhanced Media Scanner v2.0 BUFF - Quick Start Guide

## Installation (One Time)

```powershell
# 1. Double-click setup.bat
#    OR run in PowerShell:
.\setup.bat

# Installs: pillow, numpy, nudenet, opencv-python
# Time: 3-5 minutes
```

## Running the Scanner

### Method 1: Interactive Menu (Easiest)
```powershell
# Double-click run_scanner.bat
# Then select:
#   [1] Standard scan (C: drive)
#   [2] Scan specific folder
#   [3] Copy files to organized folders
#   [4] Move files to organized folders
#   [5] Show help
```

### Method 2: Command Line (Flexible)
```powershell
# Standard scan with confirmation
py -3.13 media_scanner.py

# Quick scan specific folder
py -3.13 media_scanner.py --scan-path D:\Pictures

# Scan and copy files (no prompts)
py -3.13 media_scanner.py --scan-path C: --mode copy --no-confirm

# Help
py -3.13 media_scanner.py --help
```

## Common Commands

### Scan Your Downloads
```powershell
py -3.13 media_scanner.py --scan-path D:\Downloads --mode copy
```

### Test With Limited Files
```powershell
py -3.13 media_scanner.py --max-files 100 --no-confirm
```

### High Sensitivity
```powershell
py -3.13 media_scanner.py --confidence 0.5 --no-confirm
```

### Filename Analysis Only (Fast)
```powershell
py -3.13 media_scanner.py --no-visual --no-confirm
```

### Save Your Settings
```powershell
py -3.13 media_scanner.py --scan-path C: --mode copy --save-config my_settings.json

# Next time, reuse them:
py -3.13 media_scanner.py --config my_settings.json --no-confirm
```

## Understanding Results

Results saved to: `Desktop/Media_Scan_Results/`

```
├── enhanced_scan_report_TIMESTAMP.json    ← Detailed analysis
├── enhanced_scan_summary_TIMESTAMP.txt    ← Human-readable summary
├── logs/scan_TIMESTAMP.log                 ← Debug information
└── Organized_Media/                        ← (if using --mode copy/move)
    ├── images/
    │   ├── sfw/          ← Safe images
    │   ├── nsfw/         ← Explicit images
    │   └── uncertain/    ← Unclear category
    ├── videos/           ← Same structure
    └── audio/            ← Same structure
```

## Troubleshooting

| Problem | Solution |
|---|---|
| "Python 3.13 not found" | Run setup.bat to install Python 3.13 |
| "NudeNet not installed" | Run setup.bat again or: `py -3.13 -m pip install nudenet` |
| "Access denied" errors | Run as Administrator |
| Slow scanning | Use `--workers 8` to increase speed (requires 8GB+ RAM) |
| Want only filename detection | Use `--no-visual` flag |

## Tips & Tricks

### Batch Processing
```powershell
# Scan multiple drives
py -3.13 media_scanner.py --scan-path D: --mode copy
py -3.13 media_scanner.py --scan-path E: --mode copy
```

### Automated Scans
```powershell
# Create a config file once
py -3.13 media_scanner.py --save-config auto_scan.json

# Then run repeatedly:
py -3.13 media_scanner.py --config auto_scan.json --no-confirm
```

### Testing
```powershell
# Test with just 10 files first
py -3.13 media_scanner.py --max-files 10 --no-confirm
```

### Performance Tuning
```powershell
# Use more workers (faster but uses more RAM)
py -3.13 media_scanner.py --workers 8

# Use fewer workers (slower but less RAM)
py -3.13 media_scanner.py --workers 2
```

## What Gets Detected

### AI Visual Analysis (Default)
- Nudity (exposed genitalia, breasts, buttocks)
- Explicit sexual content
- Confidence scores for accuracy

### Filename Detection (Fallback)
- 70+ keywords (NSFW, porn, nude, xxx, etc.)
- Safe indicators (screenshot, document, family, etc.)
- Works without NudeNet

## Safety Notes

✅ **100% Local** - No uploading to cloud
✅ **Read-Only Default** - Original files never modified
✅ **Copy Mode** - Creates separate organized folder
✅ **Move Mode** - Reorganizes existing files
✅ **Reversible** - Use copy mode if unsure

## Performance

Typical times on modern PC (with AI analysis):
- 1,000 files: 5-10 minutes
- 5,000 files: 25-50 minutes
- 10,000 files: 50-100 minutes

Use `--max-files 5000` to split large drives into batches.

## Getting Help

1. **Command help:** `py -3.13 media_scanner.py --help`
2. **Full docs:** See README.md
3. **Troubleshooting:** See docs/TROUBLESHOOTING.md
4. **Architecture:** See CLAUDE.md

## Version Info

- **Version:** 2.0 BUFF
- **Python Required:** 3.13
- **Status:** Production Ready ✅
- **License:** Personal Use
