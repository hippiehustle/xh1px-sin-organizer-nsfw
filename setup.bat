@echo off
REM Enhanced Media Scanner v2.0 - Dependency Setup
REM Robust installation with error handling and validation

setlocal enabledelayedexpansion

echo.
echo =====================================================
echo  Enhanced Media Scanner v2.0 BUFF
echo  One-Click Setup (Python 3.13 Required)
echo =====================================================
echo.

REM Check Python 3.13 installation
py -3.13 --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.13 not found!
    echo.
    echo Available Python versions on your system:
    py -0
    echo.
    echo [ACTION REQUIRED]
    echo 1. Download Python 3.13 from: https://www.python.org/downloads/
    echo 2. During installation, check "Add Python 3.13 to PATH"
    echo 3. Run this setup script again
    echo.
    pause
    exit /b 1
)

REM Get Python version for confirmation
for /f "tokens=*" %%i in ('py -3.13 --version') do set PYTHON_VERSION=%%i
echo [OK] Found: %PYTHON_VERSION%
echo.

REM Display installation plan
echo [*] Installation Plan:
echo     1. Upgrade pip package manager
echo     2. Core dependencies (pillow, numpy)
echo     3. NudeNet (AI visual analysis engine)
echo     4. OpenCV (video frame extraction)
echo.
echo [*] Estimated time: 3-5 minutes (depends on internet speed)
echo [*] Requires: ~500MB disk space
echo.

set /p confirm="Continue with installation? (Y/n): "
if /i "%confirm%"=="n" (
    echo Installation cancelled
    pause
    exit /b 0
)

echo.
echo =====================================================
echo  Installing Dependencies...
echo =====================================================
echo.

REM Step 1: Upgrade pip
echo [1/4] Upgrading pip package manager...
py -3.13 -m pip install --upgrade pip
if errorlevel 1 (
    echo [WARNING] pip upgrade had issues, continuing...
)

REM Step 2: Core dependencies
echo.
echo [2/4] Installing core dependencies (pillow, numpy)...
py -3.13 -m pip install pillow numpy
if errorlevel 1 (
    echo [ERROR] Failed to install core dependencies
    pause
    exit /b 1
)

REM Step 3: NudeNet
echo.
echo [3/4] Installing NudeNet (AI visual analysis)...
echo [NOTE] This step may take a few minutes...
py -3.13 -m pip install nudenet
if errorlevel 1 (
    echo [WARNING] NudeNet installation failed. Visual analysis will not work.
    echo [INFO] The scanner will fall back to filename-based detection
)

REM Step 4: OpenCV
echo.
echo [4/4] Installing OpenCV (video analysis)...
py -3.13 -m pip install opencv-python
if errorlevel 1 (
    echo [WARNING] OpenCV installation failed. Video analysis will be disabled.
    echo [INFO] The scanner will still work for images and filename analysis
)

echo.
echo =====================================================
echo  Installation Complete!
echo =====================================================
echo.
echo [OK] Setup finished successfully!
echo.
echo Next steps:
echo   1. Double-click run_scanner.bat to start scanning
echo   2. Or use command line: py -3.13 media_scanner.py [options]
echo.
echo For help with command-line options:
echo   py -3.13 media_scanner.py --help
echo.
pause
