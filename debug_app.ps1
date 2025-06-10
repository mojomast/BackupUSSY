<#
.SYNOPSIS
    Debug BackupUSSY Application

.DESCRIPTION
    Comprehensive debugging script to identify and diagnose issues with BackupUSSY.
    Tests both source and binary versions.

.PARAMETER TestBinary
    Test the compiled binary version

.PARAMETER TestSource
    Test the source version

.PARAMETER Verbose
    Enable verbose output

.EXAMPLE
    .\debug_app.ps1 -TestBinary -Verbose
#>

param(
    [switch]$TestBinary = $false,
    [switch]$TestSource = $false,
    [switch]$Verbose = $false
)

# Color functions
function Write-Debug { param($Message) Write-Host "[DEBUG] $Message" -ForegroundColor Magenta }
function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

function Test-Prerequisites {
    Write-Debug "Testing prerequisites..."
    
    # Test Python
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python: $pythonVersion"
        } else {
            Write-Error "Python not found in PATH"
        }
    } catch {
        Write-Error "Python test failed: $_"
    }
    
    # Test virtual environment
    if (Test-Path ".venv\Scripts\python.exe") {
        Write-Success "Virtual environment found"
        
        # Test FreeSimpleGUI
        try {
            $fsgTest = & ".venv\Scripts\python.exe" -c "import FreeSimpleGUI as sg; print('FreeSimpleGUI version:', sg.version); print('Has Window:', hasattr(sg, 'Window'))"
            if ($LASTEXITCODE -eq 0) {
                Write-Success "FreeSimpleGUI: $fsgTest"
            } else {
                Write-Error "FreeSimpleGUI test failed"
            }
        } catch {
            Write-Error "FreeSimpleGUI import test failed: $_"
        }
    } else {
        Write-Warning "Virtual environment not found"
    }
    
    # Test dependencies
    Write-Debug "Testing system dependencies..."
    @('tar', 'dd') | ForEach-Object {
        try {
            $null = & $_ --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "$_ found in PATH"
            } else {
                Write-Warning "$_ not found or not working"
            }
        } catch {
            Write-Warning "$_ not available: $_"
        }
    }
}

function Test-SourceImports {
    Write-Debug "Testing source module imports..."
    
    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        Write-Error "Virtual environment not found. Run install.ps1 first."
        return $false
    }
    
    $venvPython = ".venv\Scripts\python.exe"
    
    # Test individual module imports
    $modules = @(
        'main',
        'archive_manager', 
        'tape_manager',
        'logger_manager',
        'database_manager',
        'recovery_manager',
        'search_interface',
        'advanced_search',
        'tape_browser',
        'tape_library'
    )
    
    $importErrors = @()
    
    foreach ($module in $modules) {
        Write-Debug "Testing import: $module"
        try {
            $result = & $venvPython -c "import sys; sys.path.insert(0, 'src'); import $module; print('OK: $module')"
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Import OK: $module"
            } else {
                Write-Error "Import failed: $module"
                $importErrors += $module
            }
        } catch {
            Write-Error "Import exception: $module - $_"
            $importErrors += $module
        }
    }
    
    return $importErrors.Count -eq 0
}

function Test-GUILaunch {
    param([string]$Mode = "source")
    
    Write-Debug "Testing GUI launch in $Mode mode..."
    
    if ($Mode -eq "source") {
        if (-not (Test-Path ".venv\Scripts\python.exe")) {
            Write-Error "Virtual environment not found"
            return $false
        }
        
        $command = ".venv\Scripts\python.exe"
        $args = @("src\gui.py")
    } else {
        if (-not (Test-Path "src\dist\BackupUSSY.exe")) {
            Write-Error "Binary not found at src\dist\BackupUSSY.exe"
            return $false
        }
        
        $command = "src\dist\BackupUSSY.exe"
        $args = @()
    }
    
    Write-Info "Launching: $command $args"
    Write-Info "This will test if the GUI opens without immediate crashes..."
    Write-Warning "Close the GUI window manually after it opens (or wait 10 seconds)"
    
    try {
        # Start the process and wait briefly
        $process = Start-Process -FilePath $command -ArgumentList $args -PassThru -WindowStyle Normal
        
        # Wait a few seconds to see if it crashes immediately
        Start-Sleep -Seconds 3
        
        if ($process.HasExited) {
            Write-Error "GUI process exited immediately with code: $($process.ExitCode)"
            return $false
        } else {
            Write-Success "GUI launched successfully (process ID: $($process.Id))"
            
            # Wait a bit more then check again
            Start-Sleep -Seconds 7
            
            if (-not $process.HasExited) {
                Write-Info "GUI still running after 10 seconds - attempting graceful close"
                try {
                    $process.CloseMainWindow()
                    Start-Sleep -Seconds 2
                    if (-not $process.HasExited) {
                        $process.Kill()
                    }
                    Write-Success "GUI test completed successfully"
                } catch {
                    Write-Warning "Could not close GUI gracefully: $_"
                }
            } else {
                Write-Error "GUI exited after initial launch with code: $($process.ExitCode)"
                return $false
            }
            
            return $true
        }
    } catch {
        Write-Error "Failed to launch GUI: $_"
        return $false
    }
}

function Test-ModuleSpecific {
    Write-Debug "Testing specific module functionality..."
    
    $venvPython = ".venv\Scripts\python.exe"
    
    # Test database initialization
    Write-Debug "Testing database initialization..."
    try {
        $dbTest = & $venvPython -c "import sys; sys.path.insert(0, 'src'); from database_manager import DatabaseManager; db = DatabaseManager(); print('Database OK')"
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Database initialization: OK"
        } else {
            Write-Error "Database initialization failed"
        }
    } catch {
        Write-Error "Database test exception: $_"
    }
    
    # Test dependency manager
    Write-Debug "Testing dependency manager..."
    try {
        $depTest = & $venvPython -c "import sys; sys.path.insert(0, 'src'); from main import DependencyManager; dm = DependencyManager(); print('Dependencies OK')"
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Dependency manager: OK"
        } else {
            Write-Error "Dependency manager failed"
        }
    } catch {
        Write-Error "Dependency manager test exception: $_"
    }
}

function Get-DetailedError {
    param([string]$Mode = "source")
    
    Write-Debug "Getting detailed error information for $Mode mode..."
    
    if ($Mode -eq "source") {
        $command = ".venv\Scripts\python.exe"
        $args = @("-c", "import sys; sys.path.insert(0, 'src'); import gui")
    } else {
        # For binary, we can't easily get detailed import errors
        Write-Info "Binary mode - running with error capture"
        $command = "src\dist\BackupUSSY.exe"
        $args = @()
    }
    
    Write-Info "Running: $command $args"
    
    try {
        $output = & $command @args 2>&1
        $exitCode = $LASTEXITCODE
        
        Write-Info "Exit code: $exitCode"
        Write-Info "Output:"
        $output | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        
        return @{
            ExitCode = $exitCode
            Output = $output
        }
    } catch {
        Write-Error "Command execution failed: $_"
        return $null
    }
}

# Main debugging routine
Write-Host "=== BackupUSSY Debug Tool ===" -ForegroundColor Magenta
Write-Host "Comprehensive application debugging" -ForegroundColor Cyan
Write-Host ""

# Test prerequisites
Test-Prerequisites
Write-Host ""

# Test source imports if requested or no specific mode
if ($TestSource -or (-not $TestBinary -and -not $TestSource)) {
    Write-Host "=== SOURCE VERSION TESTING ===" -ForegroundColor Yellow
    
    if (Test-SourceImports) {
        Write-Success "All source imports successful"
        
        # Test specific modules
        Test-ModuleSpecific
        
        # Test GUI launch
        Write-Host ""
        Write-Info "Testing GUI launch (source version)..."
        $sourceGUIResult = Test-GUILaunch -Mode "source"
        
        if (-not $sourceGUIResult) {
            Write-Host ""
            Write-Info "Getting detailed error information..."
            $errorDetails = Get-DetailedError -Mode "source"
        }
    } else {
        Write-Error "Source import tests failed"
        $errorDetails = Get-DetailedError -Mode "source"
    }
    
    Write-Host ""
}

# Test binary if requested
if ($TestBinary) {
    Write-Host "=== BINARY VERSION TESTING ===" -ForegroundColor Yellow
    
    Write-Info "Testing binary launch..."
    $binaryGUIResult = Test-GUILaunch -Mode "binary"
    
    if (-not $binaryGUIResult) {
        Write-Host ""
        Write-Info "Getting detailed binary error information..."
        $binaryErrorDetails = Get-DetailedError -Mode "binary"
    }
    
    Write-Host ""
}

# Summary
Write-Host "=== DEBUGGING SUMMARY ===" -ForegroundColor Magenta
Write-Host "Check the output above for specific errors and issues." -ForegroundColor Cyan
Write-Host "Common issues:" -ForegroundColor Yellow
Write-Host "  - PySimpleGUI import problems" -ForegroundColor White
Write-Host "  - Missing dependencies (tar, dd)" -ForegroundColor White  
Write-Host "  - Module import errors" -ForegroundColor White
Write-Host "  - Path or environment issues" -ForegroundColor White
Write-Host ""

