@echo off
REM BackupUSSY Launcher
REM Adds bundled tools to PATH and launches the application

echo Starting BackupUSSY v0.1.5.1...

REM Add bundled tools to PATH for this session
set "PATH=%~dp0bin;%PATH%"

REM Launch BackupUSSY
"%~dp0backupussy-v0.2.0.exe"

if errorlevel 1 (
    echo.
    echo BackupUSSY exited with an error.
    pause
)

