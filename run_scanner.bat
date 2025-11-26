@echo off
REM Enhanced Media Scanner v2.0 BUFF - Smart Launch Script
REM Provides interactive menu for common scanning scenarios

setlocal enabledelayedexpansion

echo.
echo =====================================================
echo  Enhanced Media Scanner v2.0 BUFF
echo  Smart Launch Tool (Python 3.13)
echo =====================================================
echo.

REM Validate Python 3.13 installation
py -3.13 --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.13 not found!
    echo.
    echo To fix:
    echo 1. Install Python 3.13 from https://www.python.org/downloads/
    echo 2. Add Python to PATH during installation
    echo 3. Run setup.bat in the scanner directory
    echo.
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=*" %%i in ('py -3.13 --version') do set PYTHON_VERSION=%%i
echo [OK] %PYTHON_VERSION% detected
echo.

REM Display menu
echo Choose scanning mode:
echo.
echo [1] Standard scan (C: drive, interactive mode)
echo [2] Quick scan specific folder
echo [3] Copy files to organized folders
echo [4] Move files to organized folders
echo [5] Show help (command-line options)
echo [6] Exit
echo.

set /p choice="Enter choice (1-6): "

if "%choice%"=="1" (
    echo.
    echo [*] Starting standard scan...
    py -3.13 media_scanner.py
    goto end
)

if "%choice%"=="2" (
    echo.
    set /p path="Enter folder path to scan: "
    if "!path!"=="" (
        echo [ERROR] No path provided
        goto end
    )
    echo [*] Scanning: !path!
    py -3.13 media_scanner.py --scan-path "!path!" --no-confirm
    goto end
)

if "%choice%"=="3" (
    echo.
    set /p path="Enter folder path to scan: "
    if "!path!"=="" (
        echo [ERROR] No path provided
        goto end
    )
    echo [*] Scanning and copying to organized folders...
    py -3.13 media_scanner.py --scan-path "!path!" --mode copy --no-confirm
    goto end
)

if "%choice%"=="4" (
    echo.
    set /p path="Enter folder path to scan: "
    if "!path!"=="" (
        echo [ERROR] No path provided
        goto end
    )
    echo [*] WARNING: This will MOVE files (cannot be undone easily)
    set /p confirm="Are you sure? (yes/no): "
    if /i "!confirm!"=="yes" (
        echo [*] Scanning and moving to organized folders...
        py -3.13 media_scanner.py --scan-path "!path!" --mode move --no-confirm
    ) else (
        echo [*] Cancelled
    )
    goto end
)

if "%choice%"=="5" (
    echo.
    py -3.13 media_scanner.py --help
    goto end
)

if "%choice%"=="6" (
    echo Exiting...
    exit /b 0
)

echo [ERROR] Invalid choice
goto end

:end
echo.
pause
