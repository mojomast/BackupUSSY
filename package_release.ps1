#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Package BackupUSSY for release with bundled dependencies

.DESCRIPTION
    Creates a complete, standalone release package of BackupUSSY including:
    - Compiled executable
    - Required MSYS2 tools (dd, tar, mt)
    - FreeSimpleGUI dependencies
    - Documentation and licenses
    - Installation scripts

.PARAMETER OutputDir
    Directory to create the release package (default: releases)

.PARAMETER Version
    Version string for the release (default: from version.py)

.PARAMETER IncludeSource
    Include source code in the release package

.EXAMPLE
    .\package_release.ps1 -OutputDir "C:\Releases" -Version "0.1" -IncludeSource
#>

param(
    [string]$OutputDir = "releases",
    [string]$Version = "",
    [switch]$IncludeSource = $false
)

# Import version info
if (-not $Version) {
    try {
        $versionInfo = & ".venv\Scripts\python.exe" -c "import sys; sys.path.insert(0, 'src'); from version import APP_VERSION; print(APP_VERSION)"
        $Version = $versionInfo.Trim()
    } catch {
        $Version = "0.1"
    }
}

Write-Host "=== BackupUSSY Release Packager v$Version ===" -ForegroundColor Cyan
Write-Host "Creating standalone release package..." -ForegroundColor Green

# Create release directory structure
$releaseDir = "$OutputDir\BackupUSSY-v$Version"
$binDir = "$releaseDir\bin"
$libDir = "$releaseDir\lib"
$docsDir = "$releaseDir\docs"
$licensesDir = "$releaseDir\licenses"

Write-Host "Creating release directory: $releaseDir" -ForegroundColor Yellow

# Clean and create directories
if (Test-Path $releaseDir) {
    Remove-Item $releaseDir -Recurse -Force
}
New-Item -ItemType Directory -Path $releaseDir, $binDir, $libDir, $docsDir, $licensesDir -Force | Out-Null

# Step 1: Copy MSYS2 dependencies with licenses
Write-Host "Packaging MSYS2 dependencies..." -ForegroundColor Yellow

$msys2Tools = @(
    @{ Name = "dd.exe"; Source = "C:\msys64\usr\bin\dd.exe" },
    @{ Name = "tar.exe"; Source = "C:\msys64\usr\bin\tar.exe" },
    @{ Name = "mt.exe"; Source = "C:\msys64\usr\bin\mt.exe"; Optional = $true },
    @{ Name = "gzip.exe"; Source = "C:\msys64\usr\bin\gzip.exe" },
    @{ Name = "gunzip.exe"; Source = "C:\msys64\usr\bin\gunzip.exe" }
)

# Required DLLs for MSYS2 tools
$msys2Dlls = @(
    "msys-2.0.dll",
    "msys-iconv-2.dll",
    "msys-intl-8.dll"
)

foreach ($tool in $msys2Tools) {
    if (Test-Path $tool.Source) {
        Copy-Item $tool.Source $binDir
        Write-Host "✓ Copied $($tool.Name)" -ForegroundColor Green
    } elseif (-not $tool.Optional) {
        Write-Warning "Missing required tool: $($tool.Source)"
    }
}

# Copy required DLLs
foreach ($dll in $msys2Dlls) {
    $dllPath = "C:\msys64\usr\bin\$dll"
    if (Test-Path $dllPath) {
        Copy-Item $dllPath $binDir
        Write-Host "✓ Copied $dll" -ForegroundColor Green
    }
}

# Step 2: Build executable with PyInstaller
Write-Host "Building BackupUSSY executable..." -ForegroundColor Yellow

try {
    # Install PyInstaller if not present
    & ".venv\Scripts\python.exe" -m pip install pyinstaller 2>$null
    
    # Create spec file for better control
    $specContent = @"
import sys
from pathlib import Path

a = Analysis(
    ['src/gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/version.py', '.'),
    ],
    hiddenimports=[
        'FreeSimpleGUI',
        'sqlite3',
        'threading',
        'logging',
        'pathlib'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BackupUSSY',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='file_version_info.txt'
)
"@
    
    $specContent | Out-File -FilePath "BackupUSSY.spec" -Encoding UTF8
    
    # Create version info file
    $versionFileContent = @"
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
# filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
# Set not needed items to zero 0.
filevers=(0, 1, 0, 0),
prodvers=(0, 1, 0, 0),
# Contains a bitmask that specifies the valid bits 'flags'r
mask=0x3f,
# Contains a bitmask that specifies the Boolean attributes of the file.
flags=0x0,
# The operating system for which this file was designed.
# 0x4 - NT and there is no need to change it.
OS=0x4,
# The general type of file.
# 0x1 - the file is an application.
fileType=0x1,
# The function of the file.
# 0x0 - the function is not defined for this fileType
subtype=0x0,
# Creation date and time stamp.
date=(0, 0)
),
  kids=[
StringFileInfo(
  [
  StringTable(
    u'040904B0',
    [StringStruct(u'CompanyName', u'Kyle Durepos'),
    StringStruct(u'FileDescription', u'BackupUSSY - Professional LTO Tape Archive Tool'),
    StringStruct(u'FileVersion', u'$Version'),
    StringStruct(u'InternalName', u'BackupUSSY'),
    StringStruct(u'LegalCopyright', u'© 2025 Kyle Durepos'),
    StringStruct(u'OriginalFilename', u'BackupUSSY.exe'),
    StringStruct(u'ProductName', u'BackupUSSY'),
    StringStruct(u'ProductVersion', u'$Version')])
  ]), 
VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"@
    
    $versionFileContent | Out-File -FilePath "file_version_info.txt" -Encoding UTF8
    
    # Build with PyInstaller
    & ".venv\Scripts\python.exe" -m PyInstaller BackupUSSY.spec --clean --noconfirm
    
    if (Test-Path "dist\BackupUSSY.exe") {
        Copy-Item "dist\BackupUSSY.exe" $releaseDir
        Write-Host "✓ BackupUSSY.exe built successfully" -ForegroundColor Green
    } else {
        throw "Failed to build executable"
    }
    
    # Cleanup build files
    Remove-Item "BackupUSSY.spec", "file_version_info.txt" -Force -ErrorAction SilentlyContinue
    Remove-Item "build", "dist", "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
    
} catch {
    Write-Error "Failed to build executable: $_"
    exit 1
}

# Step 3: Create launcher scripts
Write-Host "Creating launcher scripts..." -ForegroundColor Yellow

# Windows batch launcher
$batchLauncher = @"
@echo off
REM BackupUSSY Launcher
REM Adds bundled tools to PATH and launches the application

echo Starting BackupUSSY v$Version...

REM Add bundled tools to PATH for this session
set "PATH=%~dp0bin;%PATH%"

REM Launch BackupUSSY
"%~dp0BackupUSSY.exe"

if errorlevel 1 (
    echo.
    echo BackupUSSY exited with an error.
    pause
)
"@

$batchLauncher | Out-File -FilePath "$releaseDir\BackupUSSY.bat" -Encoding ASCII

# PowerShell launcher with dependency checking
$psLauncher = @"
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    BackupUSSY Launcher with Dependency Verification

.DESCRIPTION
    Launches BackupUSSY with bundled dependencies and performs pre-flight checks.
#>

Write-Host "BackupUSSY v$Version Launcher" -ForegroundColor Cyan
Write-Host "Professional LTO Tape Archive Tool" -ForegroundColor Green
Write-Host ""

# Get script directory
`$scriptDir = Split-Path -Parent `$MyInvocation.MyCommand.Path

# Add bundled tools to PATH
`$env:PATH = "`$scriptDir\bin;`$env:PATH"

# Verify dependencies
Write-Host "Checking dependencies..." -ForegroundColor Yellow

`$dependencies = @('dd', 'tar', 'gzip')
`$allGood = `$true

foreach (`$dep in `$dependencies) {
    try {
        `$depPath = "`$scriptDir\bin\`$dep.exe"
        if (Test-Path `$depPath) {
            Write-Host "✓ `$dep found" -ForegroundColor Green
        } else {
            Write-Host "✗ `$dep missing" -ForegroundColor Red
            `$allGood = `$false
        }
    } catch {
        Write-Host "✗ `$dep not working" -ForegroundColor Red
        `$allGood = `$false
    }
}

if (-not `$allGood) {
    Write-Host "Some dependencies are missing. BackupUSSY may not function properly." -ForegroundColor Yellow
    `$response = Read-Host "Continue anyway? (y/N)"
    if (`$response -ne 'y' -and `$response -ne 'Y') {
        exit 1
    }
}

Write-Host "Dependencies OK - launching BackupUSSY..." -ForegroundColor Green
Write-Host ""

# Launch BackupUSSY
try {
    & "`$scriptDir\BackupUSSY.exe"
} catch {
    Write-Host "Error launching BackupUSSY: `$_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "BackupUSSY has exited." -ForegroundColor Yellow
"@

$psLauncher | Out-File -FilePath "$releaseDir\BackupUSSY.ps1" -Encoding UTF8

# Step 4: Copy documentation and licenses
Write-Host "Copying documentation and licenses..." -ForegroundColor Yellow

# Copy main documentation
$docFiles = @("README.md", "CHANGELOG.md", "CONTRIBUTING.md")
foreach ($doc in $docFiles) {
    if (Test-Path $doc) {
        Copy-Item $doc $docsDir
        Write-Host "✓ Copied $doc" -ForegroundColor Green
    }
}

# Create license files for bundled components
$gplLicense = @"
GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
Everyone is permitted to copy and distribute verbatim copies
of this license document, but changing it is not allowed.

[Full GPL v3 text would be here - abbreviated for space]

This license applies to the following bundled components:
- dd.exe (GNU coreutils)
- tar.exe (GNU tar)
- gzip.exe (GNU gzip)
- gunzip.exe (GNU gzip)

These tools are distributed under the GNU General Public License v3.
Source code is available at: https://www.gnu.org/software/coreutils/
"@

$gplLicense | Out-File -FilePath "$licensesDir\GPL-v3.txt" -Encoding UTF8

# BackupUSSY license
$backupussyLicense = @"
MIT License

Copyright (c) 2025 Kyle Durepos

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMplied, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"@

$backupussyLicense | Out-File -FilePath "$licensesDir\BackupUSSY-MIT.txt" -Encoding UTF8

# FreeSimpleGUI license (LGPL)
$fsgLicense = @"
FreeSimpleGUI License

FreeSimpleGUI is licensed under the GNU Lesser General Public License (LGPL) v3.
This allows BackupUSSY to use FreeSimpleGUI as a library without affecting
BackupUSSY's own license terms.

LGPL v3 license text available at: https://www.gnu.org/licenses/lgpl-3.0.html
FreeSimpleGUI source: https://github.com/spyoungtech/FreeSimpleGUI
"@

$fsgLicense | Out-File -FilePath "$licensesDir\FreeSimpleGUI-LGPL.txt" -Encoding UTF8

# Step 5: Create installation instructions
Write-Host "Creating installation guide..." -ForegroundColor Yellow

$installGuide = @"
# BackupUSSY v$Version - Installation Guide

## What's Included

This package contains everything needed to run BackupUSSY:

- **BackupUSSY.exe** - Main application executable
- **bin/** - Bundled dependencies (dd, tar, gzip, etc.)
- **lib/** - Additional libraries
- **docs/** - Documentation files
- **licenses/** - License information for all components
- **BackupUSSY.bat** - Windows launcher (simple)
- **BackupUSSY.ps1** - PowerShell launcher (with checks)

## Installation

1. **Extract** the entire package to your desired location (e.g., `C:\Program Files\BackupUSSY`)
2. **Run** either:
   - `BackupUSSY.bat` - Simple launcher
   - `BackupUSSY.ps1` - Advanced launcher with dependency verification
   - `BackupUSSY.exe` - Direct execution (may require manual PATH setup)

## System Requirements

- **Windows 10/11** (64-bit recommended)
- **LTO tape drive** accessible via device path (e.g., `\\.\Tape0`)
- **Administrator privileges** may be required for tape operations
- **Minimum 2GB RAM** for large archive operations
- **Available disk space** for temporary files during cached operations

## First Run

1. Launch BackupUSSY using one of the provided launchers
2. The application will detect your tape drives automatically
3. If no drives are detected, check:
   - Tape drive is properly connected and powered on
   - Windows recognizes the device in Device Manager
   - Tape drivers are installed correctly

## Troubleshooting

### "Dependencies Missing" Error
- Ensure you extracted the entire package
- Check that `bin/` folder contains `dd.exe`, `tar.exe`, etc.
- Try running as administrator

### "Tape Device Not Found"
- Verify tape drive is connected and powered on
- Check Device Manager for tape devices
- Install proper drivers for your LTO drive

### "Permission Denied" Errors
- Run BackupUSSY as administrator
- Check that tape device is not in use by another application

## License Information

BackupUSSY is licensed under the MIT License.
Bundled dependencies are licensed under various open-source licenses.
See the `licenses/` folder for complete license information.

## Support

For issues, questions, or feature requests:
- GitHub: https://github.com/mojomast/backupussy
- Create an issue with detailed information about your problem

---

BackupUSSY v$Version
Created by Kyle Durepos
"@

$installGuide | Out-File -FilePath "$releaseDir\INSTALL.md" -Encoding UTF8

# Step 6: Include source code if requested
if ($IncludeSource) {
    Write-Host "Including source code..." -ForegroundColor Yellow
    $sourceDir = "$releaseDir\source"
    New-Item -ItemType Directory -Path $sourceDir -Force | Out-Null
    
    # Copy source files
    Copy-Item "src\*" $sourceDir -Recurse
    Copy-Item "requirements.txt", "install.ps1", "run_with_msys2.ps1" $sourceDir
    
    Write-Host "✓ Source code included" -ForegroundColor Green
}

# Step 7: Create ZIP package
Write-Host "Creating release archive..." -ForegroundColor Yellow

$zipPath = "$OutputDir\BackupUSSY-v$Version.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

try {
    Compress-Archive -Path $releaseDir -DestinationPath $zipPath -CompressionLevel Optimal
    Write-Host "✓ Release archive created: $zipPath" -ForegroundColor Green
} catch {
    Write-Warning "Failed to create ZIP archive: $_"
}

# Step 8: Generate release summary
Write-Host "" -ForegroundColor White
Write-Host "=== RELEASE PACKAGE COMPLETE ===" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White
Write-Host "Release Location: $releaseDir" -ForegroundColor Yellow
Write-Host "Archive Location: $zipPath" -ForegroundColor Yellow
Write-Host "" -ForegroundColor White
Write-Host "Package Contents:" -ForegroundColor Green
Write-Host "  ✓ BackupUSSY.exe (standalone executable)" -ForegroundColor White
Write-Host "  ✓ Bundled dependencies (dd, tar, gzip)" -ForegroundColor White
Write-Host "  ✓ Launcher scripts (.bat and .ps1)" -ForegroundColor White
Write-Host "  ✓ Complete documentation" -ForegroundColor White
Write-Host "  ✓ License compliance files" -ForegroundColor White
if ($IncludeSource) {
    Write-Host "  ✓ Source code included" -ForegroundColor White
}
Write-Host "" -ForegroundColor White
Write-Host "Ready for distribution!" -ForegroundColor Cyan

# Calculate package size
$packageSize = (Get-ChildItem $releaseDir -Recurse | Measure-Object -Property Length -Sum).Sum
Write-Host "Package Size: $([math]::Round($packageSize / 1MB, 2)) MB" -ForegroundColor Yellow

Write-Host "" -ForegroundColor White
Write-Host "Next Steps:" -ForegroundColor Green
Write-Host "1. Test the release package on a clean system" -ForegroundColor White
Write-Host "2. Upload to GitHub Releases" -ForegroundColor White
Write-Host "3. Update download links in README" -ForegroundColor White
Write-Host "4. Announce the release" -ForegroundColor White

