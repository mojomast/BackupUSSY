#!/usr/bin/env powershell
<#
.SYNOPSIS
    Creates a release package for BackupUSSY

.DESCRIPTION
    This script creates a distribution package for BackupUSSY, excluding development files
    and including only the necessary components for end users.

.PARAMETER Version
    Version number for the release (e.g., "1.0.0")

.PARAMETER OutputPath
    Path where the release package will be created (default: .\releases)

.EXAMPLE
    .\create_release.ps1 -Version "1.0.0"
    .\create_release.ps1 -Version "1.0.0" -OutputPath "C:\Releases"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputPath = ".\releases"
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-Prerequisites {
    Write-ColorOutput "🔍 Checking prerequisites..." $InfoColor
    
    # Check if Python is available
    try {
        $pythonVersion = python --version 2>&1
        Write-ColorOutput "✅ Python found: $pythonVersion" $SuccessColor
    } catch {
        Write-ColorOutput "❌ Python not found. Please install Python 3.7+" $ErrorColor
        return $false
    }
    
    # Check if virtual environment exists
    if (Test-Path ".venv\Scripts\python.exe") {
        Write-ColorOutput "✅ Virtual environment found" $SuccessColor
    } else {
        Write-ColorOutput "⚠️  Virtual environment not found. Run install.ps1 first" $WarningColor
    }
    
    return $true
}

function New-ReleaseDirectory {
    param([string]$ReleasePath)
    
    Write-ColorOutput "📁 Creating release directory: $ReleasePath" $InfoColor
    
    if (Test-Path $ReleasePath) {
        Write-ColorOutput "⚠️  Release directory exists, removing..." $WarningColor
        Remove-Item $ReleasePath -Recurse -Force
    }
    
    New-Item -ItemType Directory -Path $ReleasePath -Force | Out-Null
    Write-ColorOutput "✅ Release directory created" $SuccessColor
}

function Copy-SourceFiles {
    param([string]$ReleasePath)
    
    Write-ColorOutput "📄 Copying source files..." $InfoColor
    
    # Copy source directory
    Copy-Item -Path "src" -Destination "$ReleasePath\src" -Recurse -Force
    Write-ColorOutput "  ✅ Source files copied" $SuccessColor
    
    # Create empty logs directory
    New-Item -ItemType Directory -Path "$ReleasePath\logs" -Force | Out-Null
    Write-ColorOutput "  ✅ Logs directory created" $SuccessColor
    
    # Create empty database directory
    New-Item -ItemType Directory -Path "$ReleasePath\database" -Force | Out-Null
    Write-ColorOutput "  ✅ Database directory created" $SuccessColor
}

function Copy-InstallationFiles {
    param([string]$ReleasePath)
    
    Write-ColorOutput "🔧 Copying installation files..." $InfoColor
    
    $installFiles = @(
        "install.ps1",
        "install.bat", 
        "launch.ps1",
        "run.bat",
        "validate_phase2.ps1"
    )
    
    foreach ($file in $installFiles) {
        if (Test-Path $file) {
            Copy-Item -Path $file -Destination $ReleasePath -Force
            Write-ColorOutput "  ✅ Copied $file" $SuccessColor
        } else {
            Write-ColorOutput "  ⚠️  File not found: $file" $WarningColor
        }
    }
}

function Copy-DocumentationFiles {
    param([string]$ReleasePath)
    
    Write-ColorOutput "📚 Copying documentation files..." $InfoColor
    
    $docFiles = @(
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "COMPLETED.md",
        "requirements.txt"
    )
    
    foreach ($file in $docFiles) {
        if (Test-Path $file) {
            Copy-Item -Path $file -Destination $ReleasePath -Force
            Write-ColorOutput "  ✅ Copied $file" $SuccessColor
        } else {
            Write-ColorOutput "  ⚠️  File not found: $file" $WarningColor
        }
    }
}

function New-VersionFile {
    param(
        [string]$ReleasePath,
        [string]$Version
    )
    
    Write-ColorOutput "📝 Creating version file..." $InfoColor
    
    $versionContent = @"
# BackupUSSY Version Information
VERSION = "$Version"
RELEASE_DATE = "$(Get-Date -Format 'yyyy-MM-dd')"
BUILD_INFO = "Release build created on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
"@
    
    $versionContent | Out-File -FilePath "$ReleasePath\version.py" -Encoding UTF8
    Write-ColorOutput "  ✅ Version file created" $SuccessColor
}

function Test-ReleasePackage {
    param([string]$ReleasePath)
    
    Write-ColorOutput "🧪 Testing release package..." $InfoColor
    
    # Check essential files
    $essentialFiles = @(
        "src\gui.py",
        "src\main.py",
        "install.ps1",
        "run.bat",
        "README.md",
        "requirements.txt"
    )
    
    $allFilesPresent = $true
    foreach ($file in $essentialFiles) {
        $fullPath = Join-Path $ReleasePath $file
        if (Test-Path $fullPath) {
            Write-ColorOutput "  ✅ Found $file" $SuccessColor
        } else {
            Write-ColorOutput "  ❌ Missing $file" $ErrorColor
            $allFilesPresent = $false
        }
    }
    
    return $allFilesPresent
}

function New-ReleaseArchive {
    param(
        [string]$ReleasePath,
        [string]$Version,
        [string]$OutputPath
    )
    
    Write-ColorOutput "📦 Creating release archive..." $InfoColor
    
    $archiveName = "backupussy-v$Version.zip"
    $archivePath = Join-Path $OutputPath $archiveName
    
    # Remove existing archive if it exists
    if (Test-Path $archivePath) {
        Remove-Item $archivePath -Force
    }
    
    # Create the archive
    try {
        Compress-Archive -Path "$ReleasePath\*" -DestinationPath $archivePath -CompressionLevel Optimal
        Write-ColorOutput "✅ Archive created: $archivePath" $SuccessColor
        
        # Show archive size
        $archiveSize = (Get-Item $archivePath).Length
        $archiveSizeMB = [math]::Round($archiveSize / 1MB, 2)
        Write-ColorOutput "  📏 Archive size: $archiveSizeMB MB" $InfoColor
        
        return $archivePath
    } catch {
        Write-ColorOutput "❌ Failed to create archive: $($_.Exception.Message)" $ErrorColor
        return $null
    }
}

function New-ReleaseNotes {
    param(
        [string]$Version,
        [string]$OutputPath
    )
    
    Write-ColorOutput "📄 Creating release notes..." $InfoColor
    
    $releaseNotes = @"
# BackupUSSY Release v$Version

## 🎯 Overview
This release contains the complete BackupUSSY LTO tape archiving solution for Windows.

## 🚀 Quick Start
1. Download and extract `backupussy-v$Version.zip`
2. Run `install.ps1` as Administrator (or `install.bat` for basic setup)
3. Launch with `run.bat`
4. Start archiving your data to LTO tapes!

## ✨ Features
- Complete GUI application with PySimpleGUI
- Stream and cached archive modes with compression
- Dual tape support for redundancy
- SQLite database with full indexing
- Advanced search and recovery capabilities
- Comprehensive logging and monitoring
- Automated installation and setup
- Full test coverage and validation

## 📋 System Requirements
- Windows 10/11 (64-bit)
- Python 3.7 or higher
- 4GB RAM (8GB recommended)
- LTO tape drive with Windows drivers
- 1GB+ free disk space

## 🛠️ Installation

### Automated Installation (Recommended)
```powershell
# Complete setup (requires Administrator)
.\install.ps1

# Basic setup (no admin required)
install.bat
```

### Manual Installation
```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python src/database_init.py

# Run tests
python src/test_runner.py
```

## 🚀 Launch
```cmd
# Quick launch
run.bat

# Or directly
.venv\Scripts\python.exe src\gui.py
```

## 📞 Support
- GitHub Issues: https://github.com/KyleDurepos/backupussy/issues
- Documentation: README.md
- Email: support@example.com

## 📜 License
MIT License - see LICENSE file for details.

---

**Created by Kyle Durepos**

*Professional LTO tape archiving for Windows environments*
"@
    
    $notesPath = Join-Path $OutputPath "RELEASE_NOTES_v$Version.md"
    $releaseNotes | Out-File -FilePath $notesPath -Encoding UTF8
    Write-ColorOutput "✅ Release notes created: $notesPath" $SuccessColor
}

# Main execution
function Main {
    Write-ColorOutput "🎉 BackupUSSY Release Creator v1.0" $InfoColor
    Write-ColorOutput "Creating release package for version $Version" $InfoColor
    Write-ColorOutput "" 
    
    # Check prerequisites
    if (-not (Test-Prerequisites)) {
        Write-ColorOutput "❌ Prerequisites check failed" $ErrorColor
        exit 1
    }
    
    # Create output directory
    if (-not (Test-Path $OutputPath)) {
        New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
    }
    
    $releaseName = "backupussy-v$Version"
    $releasePath = Join-Path $OutputPath $releaseName
    
    try {
        # Create release directory
        New-ReleaseDirectory -ReleasePath $releasePath
        
        # Copy files
        Copy-SourceFiles -ReleasePath $releasePath
        Copy-InstallationFiles -ReleasePath $releasePath
        Copy-DocumentationFiles -ReleasePath $releasePath
        
        # Create version file
        New-VersionFile -ReleasePath $releasePath -Version $Version
        
        # Test package
        if (-not (Test-ReleasePackage -ReleasePath $releasePath)) {
            Write-ColorOutput "❌ Release package validation failed" $ErrorColor
            exit 1
        }
        
        # Create archive
        $archivePath = New-ReleaseArchive -ReleasePath $releasePath -Version $Version -OutputPath $OutputPath
        if (-not $archivePath) {
            Write-ColorOutput "❌ Failed to create release archive" $ErrorColor
            exit 1
        }
        
        # Create release notes
        New-ReleaseNotes -Version $Version -OutputPath $OutputPath
        
        # Success summary
        Write-ColorOutput "" 
        Write-ColorOutput "🎉 Release package created successfully!" $SuccessColor
        Write-ColorOutput "" 
        Write-ColorOutput "📦 Package: $archivePath" $InfoColor
        Write-ColorOutput "📁 Directory: $releasePath" $InfoColor
        Write-ColorOutput "📄 Notes: RELEASE_NOTES_v$Version.md" $InfoColor
        Write-ColorOutput "" 
        Write-ColorOutput "Next steps:" $InfoColor
        Write-ColorOutput "1. Test the release package" $InfoColor
        Write-ColorOutput "2. Upload to GitHub releases" $InfoColor
        Write-ColorOutput "3. Update documentation if needed" $InfoColor
        Write-ColorOutput "" 
        
    } catch {
        Write-ColorOutput "❌ Error creating release: $($_.Exception.Message)" $ErrorColor
        exit 1
    }
}

# Run the main function
Main

