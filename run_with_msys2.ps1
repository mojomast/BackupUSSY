#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Launch BackupUSSY with MSYS2 dependencies in PATH

.DESCRIPTION
    This script adds MSYS2 tools to PATH and launches BackupUSSY.
    Ensures dd.exe and GNU tar are available for tape operations.

.EXAMPLE
    .\run_with_msys2.ps1
#>

Write-Host "Starting BackupUSSY with MSYS2 dependencies..." -ForegroundColor Green

# Add MSYS2 tools to PATH for this session
$env:PATH = "C:\msys64\usr\bin;$env:PATH"

# Verify dependencies are available
Write-Host "Checking dependencies..." -ForegroundColor Cyan

try {
    $null = & "C:\msys64\usr\bin\dd.exe" --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ dd.exe found" -ForegroundColor Green
    } else {
        throw "dd.exe not working"
    }
} catch {
    Write-Host "✗ ERROR: dd.exe not found or not working" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    $null = & "C:\msys64\usr\bin\tar.exe" --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ GNU tar found" -ForegroundColor Green
    } else {
        throw "tar.exe not working"
    }
} catch {
    Write-Host "✗ ERROR: GNU tar not found or not working" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Dependencies OK - launching BackupUSSY..." -ForegroundColor Green
Write-Host ""

# Launch the application
try {
    & ".venv\Scripts\python.exe" "src\gui.py"
} catch {
    Write-Host "Error launching BackupUSSY: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "BackupUSSY has exited." -ForegroundColor Yellow
Read-Host "Press Enter to close"

