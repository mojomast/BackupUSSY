#!/usr/bin/env powershell
<#
.SYNOPSIS
    LTO Tape Archive Tool - Automated Installation Script

.DESCRIPTION
    This script automatically installs all dependencies for the LTO Tape Archive Tool:
    - Checks Python installation
    - Downloads and installs MSYS2 if needed
    - Installs required MSYS2 packages (tar, dd, mt)
    - Sets up Python virtual environment
    - Installs Python dependencies
    - Runs functionality tests

.PARAMETER Force
    Force reinstallation of components even if they exist

.PARAMETER SkipMSYS2
    Skip MSYS2 installation (use existing or system tools)

.PARAMETER TestOnly
    Only run the test suite without installing anything

.EXAMPLE
    .\install.ps1
    Standard installation

.EXAMPLE
    .\install.ps1 -Force
    Force reinstall all components

.EXAMPLE
    .\install.ps1 -SkipMSYS2
    Skip MSYS2 installation
#>

param(
    [switch]$Force = $false,
    [switch]$SkipMSYS2 = $false,
    [switch]$TestOnly = $false
)

# Script configuration
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"  # Speeds up downloads

# Color functions for better output
function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Step { param($Message) Write-Host "[STEP] $Message" -ForegroundColor Blue }

# Global variables
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = $SCRIPT_DIR
$PYTHON_MIN_VERSION = [Version]"3.7"
$MSYS2_INSTALL_DIR = "C:\msys64"
$MSYS2_DOWNLOAD_URL = "https://github.com/msys2/msys2-installer/releases/latest/download/msys2-x86_64-latest.exe"

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-PythonInstallation {
    Write-Step "Checking Python installation..."
    
    try {
        $pythonVersion = & python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Python not found in PATH"
        }
        
        # Parse version
        $versionString = $pythonVersion -replace "Python ", ""
        $version = [Version]$versionString
        
        if ($version -lt $PYTHON_MIN_VERSION) {
            throw "Python version $version is too old. Minimum required: $PYTHON_MIN_VERSION"
        }
        
        Write-Success "Python $version found"
        return $true
    }
    catch {
        Write-Error "Python installation issue: $_"
        Write-Info "Please install Python $PYTHON_MIN_VERSION or newer from https://python.org"
        Write-Info "Make sure to check 'Add Python to PATH' during installation"
        return $false
    }
}

function Install-MSYS2 {
    Write-Step "Installing MSYS2..."
    
    # Check if MSYS2 is already installed
    if ((Test-Path $MSYS2_INSTALL_DIR) -and -not $Force) {
        Write-Info "MSYS2 already installed at $MSYS2_INSTALL_DIR"
        return $true
    }
    
    # Check if running as administrator
    if (-not (Test-Administrator)) {
        Write-Error "MSYS2 installation requires administrator privileges"
        Write-Info "Please run this script as Administrator or use -SkipMSYS2 flag"
        return $false
    }
    
    try {
        # Download MSYS2 installer
        $installerPath = "$env:TEMP\msys2-installer.exe"
        Write-Info "Downloading MSYS2 installer..."
        
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($MSYS2_DOWNLOAD_URL, $installerPath)
        
        if (-not (Test-Path $installerPath)) {
            throw "Failed to download MSYS2 installer"
        }
        
        # Run installer silently
        Write-Info "Running MSYS2 installer (this may take a few minutes)..."
        $process = Start-Process -FilePath $installerPath -ArgumentList "install", "--confirm-command", "--accept-messages", "--root", "C:\" -Wait -PassThru
        
        if ($process.ExitCode -ne 0) {
            throw "MSYS2 installer failed with exit code $($process.ExitCode)"
        }
        
        # Clean up installer
        Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
        
        Write-Success "MSYS2 installed successfully"
        return $true
    }
    catch {
        Write-Error "Failed to install MSYS2: $_"
        return $false
    }
}

function Install-MSYS2Packages {
    Write-Step "Installing MSYS2 packages (tar, dd, mt)..."
    
    $msys2Bash = "$MSYS2_INSTALL_DIR\usr\bin\bash.exe"
    
    if (-not (Test-Path $msys2Bash)) {
        Write-Error "MSYS2 bash not found at $msys2Bash"
        return $false
    }
    
    try {
        # Update package database
        Write-Info "Updating MSYS2 package database..."
        & $msys2Bash -lc "pacman -Sy --noconfirm"
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to update MSYS2 package database"
        }
        
        # Install required packages
        Write-Info "Installing tar, coreutils (dd), and mt-st..."
        & $msys2Bash -lc "pacman -S --noconfirm tar coreutils mt-st"
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install MSYS2 packages"
        }
        
        Write-Success "MSYS2 packages installed successfully"
        return $true
    }
    catch {
        Write-Error "Failed to install MSYS2 packages: $_"
        return $false
    }
}

function Add-MSYS2ToPath {
    Write-Step "Adding MSYS2 to system PATH..."
    
    $msys2BinPath = "$MSYS2_INSTALL_DIR\usr\bin"
    
    # Get current PATH
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    
    # Check if already in PATH
    if ($currentPath -split ";" | Where-Object { $_ -eq $msys2BinPath }) {
        Write-Info "MSYS2 already in system PATH"
        return $true
    }
    
    try {
        # Add to system PATH
        $newPath = "$currentPath;$msys2BinPath"
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
        
        # Update current session PATH
        $env:PATH = "$env:PATH;$msys2BinPath"
        
        Write-Success "MSYS2 added to system PATH"
        Write-Info "You may need to restart your terminal for PATH changes to take effect"
        return $true
    }
    catch {
        Write-Error "Failed to add MSYS2 to PATH: $_"
        Write-Info "You can manually add '$msys2BinPath' to your system PATH"
        return $false
    }
}

function Setup-PythonEnvironment {
    Write-Step "Setting up Python virtual environment..."
    
    $venvPath = "$PROJECT_ROOT\.venv"
    
    try {
        # Create virtual environment if it doesn't exist
        if (-not (Test-Path $venvPath) -or $Force) {
            if (Test-Path $venvPath) {
                Write-Info "Removing existing virtual environment..."
                Remove-Item $venvPath -Recurse -Force
            }
            
            Write-Info "Creating Python virtual environment..."
            & python -m venv $venvPath
            
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to create virtual environment"
            }
        } else {
            Write-Info "Virtual environment already exists"
        }
        
        # Activate virtual environment and install packages
        $activateScript = "$venvPath\Scripts\Activate.ps1"
        if (-not (Test-Path $activateScript)) {
            throw "Virtual environment activation script not found"
        }
        
        Write-Info "Activating virtual environment and installing packages..."
        
        # Install packages using the venv python directly
        $venvPython = "$venvPath\Scripts\python.exe"
        & $venvPython -m pip install --upgrade pip
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to upgrade pip"
        }
        
        # Install requirements
        $requirementsFile = "$PROJECT_ROOT\requirements.txt"
        if (Test-Path $requirementsFile) {
            & $venvPython -m pip install -r $requirementsFile
            
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to install Python requirements"
            }
        } else {
            # Install PySimpleGUI directly if requirements.txt doesn't exist
            & $venvPython -m pip install PySimpleGUI==5.0.8.3
            
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to install PySimpleGUI"
            }
        }
        
        Write-Success "Python environment set up successfully"
        return $true
    }
    catch {
        Write-Error "Failed to set up Python environment: $_"
        return $false
    }
}

function Test-Installation {
    Write-Step "Running functionality tests..."
    
    $venvPython = "$PROJECT_ROOT\.venv\Scripts\python.exe"
    $testScript = "$PROJECT_ROOT\src\test_runner.py"
    
    if (-not (Test-Path $venvPython)) {
        Write-Error "Virtual environment Python not found"
        return $false
    }
    
    if (-not (Test-Path $testScript)) {
        Write-Error "Test script not found at $testScript"
        return $false
    }
    
    try {
        Write-Info "Running test suite..."
        
        # Change to project directory and run tests
        Push-Location $PROJECT_ROOT
        
        $testOutput = & $venvPython $testScript 2>&1
        $testExitCode = $LASTEXITCODE
        
        Pop-Location
        
        # Display test output
        $testOutput | ForEach-Object { Write-Host $_ }
        
        if ($testExitCode -eq 0) {
            Write-Success "All tests passed! Installation completed successfully."
            return $true
        } else {
            Write-Warning "Some tests failed, but core functionality may still work."
            Write-Info "Check the test output above for details."
            return $false
        }
    }
    catch {
        Write-Error "Failed to run tests: $_"
        return $false
    }
}

function Show-InstallationSummary {
    Write-Host ""
    Write-Host "=== LTO Tape Archive Tool Installation Summary ===" -ForegroundColor Magenta
    Write-Host ""
    
    # Check what's installed
    $pythonOk = Test-PythonInstallation 2>$null
    $msys2Ok = Test-Path "$MSYS2_INSTALL_DIR\usr\bin\tar.exe"
    $venvOk = Test-Path "$PROJECT_ROOT\.venv\Scripts\python.exe"
    
    Write-Host "Component Status:" -ForegroundColor Yellow
    Write-Host "  Python:        $(if($pythonOk) {'✓ Installed'} else {'✗ Missing'})" -ForegroundColor $(if($pythonOk) {'Green'} else {'Red'})
    Write-Host "  MSYS2:         $(if($msys2Ok) {'✓ Installed'} else {'✗ Missing'})" -ForegroundColor $(if($msys2Ok) {'Green'} else {'Red'})
    Write-Host "  Virtual Env:   $(if($venvOk) {'✓ Created'} else {'✗ Missing'})" -ForegroundColor $(if($venvOk) {'Green'} else {'Red'})
    
    Write-Host ""
    Write-Host "To start the application:" -ForegroundColor Yellow
    Write-Host "  1. Open PowerShell in the project directory"
    Write-Host "  2. Run: .venv\Scripts\python.exe src\gui.py" -ForegroundColor Green
    Write-Host ""
    Write-Host "To run tests:" -ForegroundColor Yellow
    Write-Host "  Run: .venv\Scripts\python.exe src\test_runner.py" -ForegroundColor Green
    Write-Host ""
    
    if (-not $msys2Ok) {
        Write-Host "Note: MSYS2 tools are required for actual tape operations." -ForegroundColor Yellow
        Write-Host "Re-run this script as Administrator to install MSYS2." -ForegroundColor Yellow
    }
}

# Main installation function
function Start-Installation {
    Write-Host "=== LTO Tape Archive Tool - Installation Script ===" -ForegroundColor Magenta
    Write-Host ""
    
    if ($TestOnly) {
        Write-Info "Running tests only..."
        Test-Installation
        return
    }
    
    $success = $true
    
    # Step 1: Check Python
    if (-not (Test-PythonInstallation)) {
        $success = $false
        Write-Info "Please install Python and run this script again."
        return
    }
    
    # Step 2: Install MSYS2 (optional)
    if (-not $SkipMSYS2) {
        if (Test-Administrator) {
            if (-not (Install-MSYS2)) {
                Write-Warning "MSYS2 installation failed, but continuing..."
            } elseif (-not (Install-MSYS2Packages)) {
                Write-Warning "MSYS2 package installation failed, but continuing..."
            } else {
                # Only add to PATH if installation succeeded
                Add-MSYS2ToPath | Out-Null
            }
        } else {
            Write-Warning "Skipping MSYS2 installation (requires administrator privileges)"
            Write-Info "Run as Administrator to install MSYS2 automatically, or install manually"
        }
    } else {
        Write-Info "Skipping MSYS2 installation as requested"
    }
    
    # Step 3: Set up Python environment
    if (-not (Setup-PythonEnvironment)) {
        $success = $false
    }
    
    # Step 4: Run tests
    Write-Host ""
    if (-not (Test-Installation)) {
        Write-Warning "Some tests failed, but installation may still be usable"
    }
    
    # Show summary
    Write-Host ""
    Show-InstallationSummary
    
    # Initialize Phase 2 Features
    Write-Host "" 
    Write-Host "🔧 Initializing Phase 2 Features..." -ForegroundColor Cyan
    
    # Create data directories
    $dataDir = Join-Path $PROJECT_ROOT "data"
    $backupsDir = Join-Path $dataDir "backups"
    $exportsDir = Join-Path $dataDir "exports"
    
    @($dataDir, $backupsDir, $exportsDir) | ForEach-Object {
        if (-not (Test-Path $_)) {
            New-Item -ItemType Directory -Path $_ -Force | Out-Null
            Write-Host "✅ Created directory: $($_ | Split-Path -Leaf)" -ForegroundColor Green
        }
    }
    
    # Test Phase 2 components
    try {
        $venvPython = Join-Path $PROJECT_ROOT ".venv\Scripts\python.exe"
        if (Test-Path $venvPython) {
            Write-Host "🧪 Testing Phase 2 components..." -ForegroundColor Yellow
            
            # Test database initialization
            $dbTest = & $venvPython -c "from src.database_manager import DatabaseManager; db = DatabaseManager(); print('Database OK')" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Database component initialized" -ForegroundColor Green
            }
            
            # Test component imports
            $importTest = & $venvPython -c "from src.recovery_manager import RecoveryManager; from src.tape_library import TapeLibrary; print('Components OK')" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Phase 2 components imported successfully" -ForegroundColor Green
            }
            
            # Run quick validation
            $testScript = Join-Path $PROJECT_ROOT "src\test_recovery.py"
            if (Test-Path $testScript) {
                Write-Host "🧪 Running quick validation..." -ForegroundColor Yellow
                $validationResult = & $venvPython $testScript --quick 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✅ Quick validation passed" -ForegroundColor Green
                } else {
                    Write-Host "⚠️ Some validation tests failed (may be expected without tape hardware)" -ForegroundColor Yellow
                }
            }
        }
    } catch {
        Write-Host "⚠️ Phase 2 testing encountered issues: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    Write-Host ""
    if ($success) {
        Write-Host "Installation completed successfully! 🎉" -ForegroundColor Green
        Write-Host ""
        Write-Host "🆕 Phase 2 Professional Features Available:" -ForegroundColor Cyan
        Write-Host "   🔄 Complete recovery system with tape reading" -ForegroundColor White
        Write-Host "   🗄️ SQLite database for file and tape indexing" -ForegroundColor White
        Write-Host "   🔍 Advanced search across all archived content" -ForegroundColor White
        Write-Host "   📋 Professional tape library management" -ForegroundColor White
        Write-Host "   🎛️ Enhanced tabbed GUI interface" -ForegroundColor White
        Write-Host "   📤 Data export/import and reporting" -ForegroundColor White
        Write-Host "   🔧 Advanced error recovery and damage detection" -ForegroundColor White
    } else {
        Write-Host "Installation completed with some issues. Check the output above." -ForegroundColor Yellow
    }
}

# Run the installation
try {
    Start-Installation
}
catch {
    Write-Error "Installation failed: $_"
    Write-Host "Please check the error message above and try again." -ForegroundColor Red
    exit 1
}

