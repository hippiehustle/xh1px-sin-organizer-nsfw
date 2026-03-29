@echo off
title Windows Media Recovery App

REM Launch focused recovery GUI for images/videos/zip files
py -3.13 windows_recovery_app.py

if %errorlevel% neq 0 (
  echo.
  echo Failed to start Recovery App.
  echo Ensure Python 3.13 is installed and available via the py launcher.
  pause
)
