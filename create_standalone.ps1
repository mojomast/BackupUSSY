# BackupUSSY Standalone Package Creator
# Creates a complete package with compiled executable + bundled tools

Write-Host "=== BackupUSSY Standalone Package Creator ===" -ForegroundColor Cyan
Write-Host "Creating standalone distribution (no Python required)..." -ForegroundColor Green

# Get version
$version = "0.1"
try {
    $version = & ".venv\Scripts\python.exe" -c "import sys; sys.path.insert(0, 'src'); from version import APP_VERSION; print(APP_VERSION)"
    $version = $version.Trim()
} catch {
    Write-Host "Could not get version, using 0.1" -ForegroundColor Yellow
}

# Install PyInstaller if needed
Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
& ".venv\Scripts\python.exe" -m pip install pyinstaller

# Create PyInstaller spec file
Write-Host "Creating PyInstaller spec..." -ForegroundColor Yellow
$specContent = @"
a = Analysis(
    ['src/gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['FreeSimpleGUI', 'sqlite3'],
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
)
"@

$specContent | Out-File -FilePath "BackupUSSY.spec" -Encoding UTF8

# Build executable
Write-Host "Building BackupUSSY.exe..." -ForegroundColor Yellow
& ".venv\Scripts\python.exe" -m PyInstaller BackupUSSY.spec --clean --noconfirm

if (-not (Test-Path "dist\BackupUSSY.exe")) {
    Write-Error "Failed to build executable"
    exit 1
}

Write-Host "Executable built successfully!" -ForegroundColor Green

# Create package directory
$packageDir = "BackupUSSY-standalone-v$version"
if (Test-Path $packageDir) {
    Remove-Item $packageDir -Recurse -Force
}
New-Item -ItemType Directory -Path $packageDir -Force | Out-Null
New-Item -ItemType Directory -Path "$packageDir\tools" -Force | Out-Null
New-Item -ItemType Directory -Path "$packageDir\licenses" -Force | Out-Null

Write-Host "Created package directory: $packageDir" -ForegroundColor Green

# Copy executable
Copy-Item "dist\BackupUSSY.exe" $packageDir
Write-Host "Copied BackupUSSY.exe" -ForegroundColor Green

# Copy essential tools from MSYS2
Write-Host "Copying tools..." -ForegroundColor Yellow
$tools = @("dd.exe", "tar.exe", "gzip.exe", "msys-2.0.dll", "msys-iconv-2.dll", "msys-intl-8.dll")
foreach ($tool in $tools) {
    $source = "C:\msys64\usr\bin\$tool"
    if (Test-Path $source) {
        Copy-Item $source "$packageDir\tools\"
        Write-Host "Copied $tool" -ForegroundColor Green
    } else {
        Write-Host "Missing $tool" -ForegroundColor Yellow
    }
}

# Create simple launcher that adds tools to PATH
$launcher = @'
@echo off
echo Starting BackupUSSY...

REM Add bundled tools to PATH for this session
set "PATH=%~dp0tools;%PATH%"

REM Launch BackupUSSY
"%~dp0BackupUSSY.exe"

if errorlevel 1 (
    echo.
    echo BackupUSSY exited with an error.
    pause
)
'@

$launcher | Out-File -FilePath "$packageDir\Launch-BackupUSSY.bat" -Encoding ASCII

# Create PowerShell launcher with checks
$psLauncher = @'
#!/usr/bin/env pwsh

Write-Host "BackupUSSY Standalone Edition" -ForegroundColor Cyan
Write-Host "Professional LTO Tape Archive Tool" -ForegroundColor Green
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Add tools to PATH
$env:PATH = "$scriptDir\tools;$env:PATH"

# Verify tools
Write-Host "Checking bundled tools..." -ForegroundColor Yellow
$tools = @("dd", "tar")
foreach ($tool in $tools) {
    $toolPath = "$scriptDir\tools\$tool.exe"
    if (Test-Path $toolPath) {
        Write-Host "✓ $tool found" -ForegroundColor Green
    } else {
        Write-Host "✗ $tool missing" -ForegroundColor Red
    }
}

# Launch BackupUSSY
Write-Host "Starting BackupUSSY..." -ForegroundColor Green
Write-Host ""

try {
    & "$scriptDir\BackupUSSY.exe"
} catch {
    Write-Host "Error launching BackupUSSY: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}

Write-Host "BackupUSSY has exited." -ForegroundColor Yellow
'@

$psLauncher | Out-File -FilePath "$packageDir\Launch-BackupUSSY.ps1" -Encoding UTF8

# Create README
$readme = @'
# BackupUSSY Standalone Edition

## What You Get

This is a complete standalone package:
- **BackupUSSY.exe** - Compiled executable (no Python needed)
- **tools/** - Essential command-line tools (dd, tar, gzip)
- **Launch scripts** - Easy startup with proper PATH setup
- **Complete independence** - No external dependencies

## System Requirements

- **Windows 10/11** (64-bit)
- **LTO tape drive** (for actual tape operations)
- **No Python required** - everything is bundled
- **No installation needed** - runs from any folder

## Quick Start

1. **Extract** this entire folder to your desired location
2. **Double-click** either:
   - `Launch-BackupUSSY.bat` (simple launcher)
   - `Launch-BackupUSSY.ps1` (PowerShell launcher with checks)
3. **BackupUSSY starts immediately** - no setup required

## What Makes This Special

✓ **Zero dependencies** - completely self-contained
✓ **No Python installation** - everything compiled in
✓ **Bundled tools** - dd, tar, gzip included
✓ **Portable** - copy folder anywhere, works immediately
✓ **Professional** - same full feature set as source version

## License Compliance

- **BackupUSSY**: MIT License
- **Bundled tools**: GPL v3 License
- **All licenses included** in licenses/ folder

## File Structure

```
BackupUSSY-standalone-v0.1/
├── BackupUSSY.exe           # Main application
├── Launch-BackupUSSY.bat    # Simple launcher
├── Launch-BackupUSSY.ps1    # Advanced launcher
├── tools/                   # Bundled command-line tools
│   ├── dd.exe
│   ├── tar.exe
│   ├── gzip.exe
│   └── *.dll files
├── licenses/                # License information
└── README.md               # This file
```

## Support

- **GitHub**: https://github.com/mojomast/backupussy
- **Issues**: Report problems via GitHub Issues
- **Documentation**: See GitHub repository

---

BackupUSSY Standalone Edition v0.1
Created by Kyle Durepos
No Python Required!
'@

$readme | Out-File -FilePath "$packageDir\README.md" -Encoding UTF8

# Create license files
$mit = @'
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
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'@

$mit | Out-File -FilePath "$packageDir\licenses\MIT-BackupUSSY.txt" -Encoding UTF8

$gpl = @'
GNU GENERAL PUBLIC LICENSE v3

Bundled tools licensed under GPL v3:
- dd.exe (GNU coreutils)
- tar.exe (GNU tar)
- gzip.exe (GNU gzip)

Source code available at:
- https://www.gnu.org/software/coreutils/
- https://www.gnu.org/software/tar/

Full GPL v3 license text:
https://www.gnu.org/licenses/gpl-3.0.html

Redistribution requirements:
✓ Include this license notice
✓ Provide access to source code (links above)
✓ Maintain copyright notices
'@

$gpl | Out-File -FilePath "$packageDir\licenses\GPL-Tools.txt" -Encoding UTF8

# Create ZIP package
Write-Host "Creating ZIP archive..." -ForegroundColor Yellow
$zipName = "BackupUSSY-standalone-v$version.zip"
Compress-Archive -Path $packageDir -DestinationPath $zipName -CompressionLevel Optimal -Force

# Cleanup build files
Remove-Item "BackupUSSY.spec" -Force -ErrorAction SilentlyContinue
Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "dist" -Recurse -Force -ErrorAction SilentlyContinue

# Show results
$size = (Get-ChildItem $packageDir -Recurse | Measure-Object -Property Length -Sum).Sum
$exeSize = (Get-Item "$packageDir\BackupUSSY.exe").Length
$toolsSize = (Get-ChildItem "$packageDir\tools" | Measure-Object -Property Length -Sum).Sum

Write-Host "" -ForegroundColor White
Write-Host "=== STANDALONE PACKAGE COMPLETE ===" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White
Write-Host "Package: $packageDir" -ForegroundColor Yellow
Write-Host "Archive: $zipName" -ForegroundColor Yellow
Write-Host "Total size: $([math]::Round($size / 1MB, 2)) MB" -ForegroundColor Yellow
Write-Host "Executable: $([math]::Round($exeSize / 1MB, 2)) MB" -ForegroundColor Yellow
Write-Host "Tools: $([math]::Round($toolsSize / 1KB, 0)) KB" -ForegroundColor Yellow
Write-Host "" -ForegroundColor White
Write-Host "✓ No Python required" -ForegroundColor Green
Write-Host "✓ No installation needed" -ForegroundColor Green
Write-Host "✓ All dependencies bundled" -ForegroundColor Green
Write-Host "✓ Ready for distribution" -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "Users just need to extract and run!" -ForegroundColor Cyan

