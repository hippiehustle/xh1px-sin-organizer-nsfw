@echo off
REM ============================================================================
REM Enhanced Media Scanner v3.0 ULTRA BUFF - GUI Launcher
REM Launches the graphical configuration interface
REM ============================================================================

echo.
echo ============================================================================
echo   ENHANCED MEDIA SCANNER v3.0 ULTRA BUFF - GUI Launcher
echo ============================================================================
echo.

REM Check if Python 3.13 is installed
py -3.13 --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.13 not found!
    echo.
    echo Please install Python 3.13 from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [*] Python 3.13 detected
echo.

REM Check if required packages are installed
echo [*] Checking dependencies...
py -3.13 -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] tkinter not available!
    echo This should be included with Python. Try reinstalling Python with tcl/tk support.
    pause
    exit /b 1
)

echo [*] GUI dependencies OK
echo.

REM Launch GUI
echo [*] Launching Enhanced Media Scanner GUI...
echo.
py -3.13 media_scanner_gui.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo [ERROR] GUI exited with error code: %ERRORLEVEL%
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [*] GUI closed successfully
echo.
pause
