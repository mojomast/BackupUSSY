#!/usr/bin/env powershell
<#
.SYNOPSIS
    Quick launcher for LTO Tape Archive Tool

.DESCRIPTION
    Launches the LTO Tape Archive Tool GUI application.
    Checks for proper installation and provides helpful error messages.

.EXAMPLE
    .\launch.ps1
    Start the GUI application
#>

# Color functions
function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

# Check if virtual environment exists
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Error "Virtual environment not found!"
    Write-Info "Please run the installation script first:"
    Write-Info "  .\install.ps1  (for full installation)"
    Write-Info "  .\install.bat  (basic setup)"
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if GUI script exists
if (-not (Test-Path "src\gui.py")) {
    Write-Error "GUI application not found at src\gui.py"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Starting LTO Tape Archive Tool - Professional Edition..." -ForegroundColor Green

try {
    # Launch the GUI application
    & ".venv\Scripts\python.exe" "src\gui.py"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Application exited with error code $LASTEXITCODE"
        Write-Info "Check the logs directory for error details"
    } else {
        Write-Success "Application closed normally"
    }
}
catch {
    Write-Error "Failed to start application: $_"
    Write-Info "Try running the test suite to diagnose issues:"
    Write-Info "  .venv\Scripts\python.exe src\test_runner.py"
}

Read-Host "Press Enter to exit"

