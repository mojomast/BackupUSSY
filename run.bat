@echo off
REM Quick launcher for LTO Tape Archive Tool

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found!
    echo Please run install.bat first
    pause
    exit /b 1
)

echo Starting LTO Tape Archive Tool - Professional Edition...
".venv\Scripts\python.exe" src\gui.py

if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)

