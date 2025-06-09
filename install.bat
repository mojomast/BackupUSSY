@echo off
setlocal EnableDelayedExpansion

echo =====================================
echo  LTO Tape Archive Tool - Quick Setup
echo =====================================
echo.

REM Check if Python is installed
echo [STEP] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.7+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo [SUCCESS] Python %PYTHON_VERSION% found

REM Check if virtual environment exists
echo.
echo [STEP] Setting up Python virtual environment...
if exist ".venv" (
    echo [INFO] Virtual environment already exists
) else (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Install Python packages
echo.
echo [STEP] Installing Python packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip
    pause
    exit /b 1
)

if exist "requirements.txt" (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
) else (
    ".venv\Scripts\python.exe" -m pip install PySimpleGUI==5.0.8.3
)

if errorlevel 1 (
    echo [ERROR] Failed to install Python packages
    pause
    exit /b 1
)

echo [SUCCESS] Python environment set up successfully

REM Check for MSYS2/tar tools
echo.
echo [STEP] Checking for tar and dd tools...
tar --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] tar not found in PATH
    set TAR_MISSING=1
) else (
    echo [SUCCESS] tar found
    set TAR_MISSING=0
)

dd --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] dd not found in PATH
    set DD_MISSING=1
) else (
    echo [SUCCESS] dd found
    set DD_MISSING=0
)

REM Run tests
echo.
echo [STEP] Running functionality tests...
echo.
".venv\Scripts\python.exe" src\test_runner.py
set TEST_RESULT=%errorlevel%

REM Show summary
echo.
echo =====================================
echo  Installation Summary
echo =====================================
echo.
echo Component Status:
echo   Python:        [OK] Installed
if %TAR_MISSING%==0 (
    echo   tar tool:      [OK] Available
) else (
    echo   tar tool:      [!!] Missing
)
if %DD_MISSING%==0 (
    echo   dd tool:       [OK] Available
) else (
    echo   dd tool:       [!!] Missing
)
echo   Virtual Env:   [OK] Created
echo.

if %TEST_RESULT%==0 (
    echo [SUCCESS] All tests passed! Installation completed successfully.
) else (
    echo [WARNING] Some tests failed, but core functionality may work.
)

echo.
echo To start the application:
echo   .venv\Scripts\python.exe src\gui.py
echo.
echo To run tests:
echo   .venv\Scripts\python.exe src\test_runner.py
echo.

if %TAR_MISSING%==1 if %DD_MISSING%==1 (
    echo [INFO] For full functionality, install MSYS2:
    echo   1. Download from: https://www.msys2.org/
    echo   2. Install and run: pacman -S tar coreutils mt-st
    echo   3. Add C:\msys64\usr\bin to your system PATH
    echo.
    echo Alternatively, run: .\install.ps1 as Administrator
)

echo.
echo Installation complete!
pause

