@echo off
REM BackupUSSY launcher with MSYS2 tools in PATH

echo Starting BackupUSSY with MSYS2 dependencies...

REM Add MSYS2 tools to PATH for this session
set "PATH=C:\msys64\usr\bin;%PATH%"

REM Verify dependencies are available
echo Checking dependencies...
C:\msys64\usr\bin\dd.exe --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: dd not found
    pause
    exit /b 1
)

C:\msys64\usr\bin\tar.exe --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: GNU tar not found
    pause
    exit /b 1
)

echo Dependencies OK - launching BackupUSSY...
echo.

REM Launch the application
.venv\Scripts\python.exe src\gui.py

echo.
echo BackupUSSY has exited.
pause

