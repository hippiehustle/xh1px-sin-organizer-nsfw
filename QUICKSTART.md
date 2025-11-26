# Quick Start Guide - Enhanced Media Scanner v3.0 ULTRA BUFF 🚀

## Get Started in 5 Minutes!

### Step 1: Installation (2 minutes)

#### Option A: Quick Install (Minimal Features)
```batch
# Just NSFW detection - fastest setup
pip install pillow numpy nudenet tensorflow opencv-python
```

#### Option B: Recommended Install (Most Features)
```batch
# NSFW + Object Detection + Colors + Quality
pip install pillow numpy nudenet tensorflow opencv-python ultralytics torch torchvision scikit-learn scipy
```

#### Option C: Full Install (Everything)
```batch
# All AI features (takes longer, ~5-10 GB)
pip install -r requirements.txt
```

---

### Step 2: Launch the GUI (30 seconds)

```batch
# Double-click this file or run:
run_gui.bat
```

**That's it!** The GUI will open and you're ready to scan.

---

### Step 3: Configure Your First Scan (2 minutes)

#### Tab 1: Basic Settings
1. **Scan Path**: Click "Browse" and select the folder to scan
   - Example: `C:\Users\YourName\Pictures`
2. **Scan subdirectories**: Keep checked (recommended)
3. **Max Files**: Leave empty for unlimited, or enter a number (e.g., 1000) to test first

#### Tab 2: AI Features
1. **Enable NSFW Detection**: ✅ (default, requires nudenet)
2. **Confidence Threshold**: 0.60 (lower = more sensitive)
3. **Optional Features** (enable if you installed them):
   - ✅ Object Detection (requires torch/ultralytics)
   - ✅ Color Analysis (requires scikit-learn)
   - ✅ Quality Metrics (no extra dependencies)
   - ⬜ Face Detection (requires face-recognition + dlib)
   - ⬜ Scene Classification (requires CLIP)

#### Tab 3: Organization
1. **Organization Mode**:
   - `Skip` = Scan only (safe, no files moved)
   - `Copy` = Copy to organized folders (recommended)
   - `Move` = Move to organized folders (faster)
2. **Organize By**: `classification` (SFW/NSFW/Uncertain)
3. **Output Directory**: Default is `Desktop/Media_Scan_Results`

#### Tab 4: Advanced
1. **Worker Threads**: 4 (default, increase for faster scans)
2. **Batch Size**: 1000 (default)
3. **Priority**: `balanced` (default)

---

### Step 4: Start Scanning! (30 seconds)

1. Click **"▶ Start Scan"** at the bottom
2. Confirm the scan when prompted
3. Watch the progress in the status bar
4. Wait for completion (time varies by file count)

**The scanner will:**
- Analyze all images, videos, and audio files
- Detect NSFW content using AI
- Apply any enabled AI features
- Generate detailed reports
- Organize files if you chose Copy/Move mode

---

### Step 5: Review Results (1 minute)

When complete, open the output folder (default: `Desktop/Media_Scan_Results`):

```
Media_Scan_Results/
├── enhanced_scan_report_20241123_143022.json    # Detailed results
├── enhanced_scan_summary_20241123_143022.txt    # Human-readable summary
├── ai_analysis_20241123_143022.json             # AI insights (NEW!)
└── Organized_Media/                              # Organized files (if Copy/Move)
    ├── images/
    │   ├── sfw/
    │   ├── nsfw/
    │   └── uncertain/
    ├── videos/
    └── audio/
```

#### Key Files:
- **Summary (TXT)**: Open with Notepad, easy to read
- **Report (JSON)**: All details, open with text editor or JSON viewer
- **AI Analysis (JSON)**: Top objects, colors, scenes detected

---

## Common Use Cases

### Use Case 1: Find NSFW Content in Downloads Folder
```
1. Launch GUI
2. Scan Path: C:\Users\YourName\Downloads
3. AI Features: Enable NSFW Detection only
4. Organization: Skip (just scan)
5. Start Scan
6. Review summary.txt for NSFW count and locations
```

### Use Case 2: Organize Photos by Date
```
1. Launch GUI
2. Scan Path: C:\Users\YourName\Pictures
3. AI Features: Enable Quality Metrics
4. Organization:
   - Mode: Copy
   - Organize By: date
   - ✅ Use Date Hierarchy (Year/Month/Day)
5. Start Scan
6. Check Organized_Media folder for date-sorted files
```

### Use Case 3: Find Photos with People
```
1. Launch GUI
2. Scan Path: C:\Photos
3. AI Features:
   - ✅ Face Detection
   - ✅ Object Detection
4. Organization: Skip
5. Start Scan
6. Open ai_analysis_[timestamp].json
7. Search for "face_count" to see photos with people
```

### Use Case 4: Sort by Color
```
1. Launch GUI
2. Scan Path: C:\Pictures
3. AI Features: ✅ Color Analysis
4. Organization:
   - Mode: Copy
   - Organize By: color
5. Start Scan
6. Check Organized_Media/images/[color_name]/ folders
```

---

## Tips & Tricks

### 💡 Test First, Then Run Full Scan
```
1. First scan: Set "Max Files: 100"
2. Review results to tune settings
3. Second scan: Remove max files limit
```

### 💡 Save Your Settings as a Profile
```
1. Configure everything
2. Click "Save Profile"
3. Name it (e.g., "My Photos Setup")
4. Next time: Click "Load Profile" → Select it
```

### 💡 Speed vs. Accuracy Trade-off
```
Fast Scan:
- Workers: 8
- Disable AI features except NSFW
- Priority: fast

Accurate Scan:
- Workers: 2-4
- Enable all AI features you need
- Priority: thorough
- Lower confidence threshold (0.4-0.5)
```

### 💡 Organize Later
```
1. First run: Mode = Skip (just scan)
2. Review results
3. Second run: Mode = Copy/Move (organize)
   - The scanner remembers analyzed files
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+S | Save Profile |
| Ctrl+O | Load Profile |
| F5 | Refresh |
| Esc | Cancel operation |

---

## Error? No Problem!

### "NudeNet not found"
```bash
pip install nudenet tensorflow
```

### "Ultralytics not found" (Object Detection)
```bash
pip install ultralytics torch torchvision
```

### "GUI won't open"
```bash
# Check Python version
py -3.13 --version

# Should show Python 3.13.x
# If not, install Python 3.13
```

### "Scan very slow"
```
1. Reduce AI features (disable face detection, audio transcription)
2. Increase worker threads (Advanced tab → Workers: 8)
3. Process smaller folders or use max files limit
```

### "Out of memory"
```
1. Reduce workers (Advanced tab → Workers: 2)
2. Disable some AI features
3. Close other applications
4. Process in batches (Max Files: 1000)
```

---

## What's Next?

After your first scan:

1. **Review Reports**: Check what was found
2. **Tune Settings**: Adjust confidence, enable more AI features
3. **Save Profile**: Don't reconfigure every time
4. **Organize Files**: Use the advanced organization features
5. **Schedule Regular Scans**: Scan new downloads weekly

---

## Advanced Features to Explore

Once comfortable with basics, try:

- **Date Hierarchies**: Organize by Year/Month/Day
- **Custom Naming**: Use templates like `{date}_{original}`
- **Multi-Criteria Sorting**: Organize by tags, quality, scenes
- **Video Scene Detection**: Find scene changes in videos
- **Audio Transcription**: Transcribe speech in audio files

---

## Command Line Power Users

Skip the GUI and use CLI for automation:

```bash
# Quick NSFW scan
py -3.13 media_scanner.py --scan-path "C:\Downloads" --no-confirm

# Full AI scan with organization
py -3.13 media_scanner.py \
    --scan-path "C:\Pictures" \
    --mode copy \
    --organize-by date \
    --workers 8 \
    --no-confirm

# Scan and save config
py -3.13 media_scanner.py \
    --scan-path "C:\Photos" \
    --save-config my_config.json

# Load config and run
py -3.13 media_scanner.py --config my_config.json
```

---

## Need Help?

1. **Read README_V3.md** for comprehensive documentation
2. **Check TROUBLESHOOTING.md** for common issues
3. **Open an issue** on GitHub
4. **Review the code** - it's well-commented!

---

**You're all set! Happy scanning! 🎉**

Remember: Start small (test folder), tune settings, then go big!
