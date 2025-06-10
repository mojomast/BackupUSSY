# 📼 BackupUSSY v0.1 - Professional LTO Tape Archive Tool

<div align="center">

![Version](https://img.shields.io/badge/version-0.1-brightgreen.svg)
![Platform](https://img.shields.io/badge/platform-windows-lightgrey.svg)
![FreeSimpleGUI](https://img.shields.io/badge/FreeSimpleGUI-5.2.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)

*Professional standalone LTO tape archiving tool - no Python installation required!*

[![Download Latest Release](https://img.shields.io/badge/Download-Latest%20Release-brightgreen?style=for-the-badge&logo=github)](https://github.com/mojomast/backupussy/releases/latest)

**🎉 Version 0.1: First Official Release**
*Previous v1.0.x were development builds leading to this stable release*

**🎉 NEW: Standalone Edition - Extract and Run!**

</div>

---

## 🎯 Overview

BackupUSSY is a comprehensive LTO tape archive solution designed for Windows environments. This tool focuses on archival (non-rotating) backups with support for writing to one or two tapes per archive job, ensuring your critical data is preserved with enterprise-grade reliability.

## ✨ Key Features

### 🖥️ **Modern GUI Interface**
- **🎨 FreeSimpleGUI**: Intuitive and user-friendly interface
- **📊 Real-time Progress**: Live progress bars and status updates
- **🔍 Device Detection**: Automatic LTO device discovery
- **🎯 One-Click Operation**: Simple workflow for complex operations
- **📱 Standalone**: No Python installation required

### 🏗️ **Flexible Archive Modes**
- **⚡ Stream Mode**: Direct streaming to tape using `tar | dd`
  - Faster execution with no intermediate files
  - Ideal for large datasets with limited disk space
- **💾 Cached Mode**: Create archive file first, then write to tape
  - Full checksum verification with SHA256
  - Allows pre-verification before tape writing
- **🔄 Dual Tape Support**: Option to create two copies (primary and backup)
- **🗜️ Compression Support**: Optional gzip compression for space efficiency

### 🛡️ **Enterprise Features**
- **📋 SQLite Database**: Complete archive indexing with searchable metadata
- **🔍 Advanced Search**: Find files across all archived tapes
- **📂 Tape Browser**: Browse tape contents without extraction
- **🔐 Recovery System**: Comprehensive file and folder recovery tools
- **📊 Statistics Tracking**: Detailed archive statistics and reporting
- **🔧 Automated Installation**: One-click setup with dependency management
- **🗃️ Export/Import**: Archive database backup and restore
- **🧪 Full Test Coverage**: Comprehensive test suite for reliability

## 🚀 Quick Start

### **Standalone Edition (Recommended) - No Python Required!**

[![Download Latest Release](https://img.shields.io/github/release/mojomast/backupussy.svg?style=flat-square)](https://github.com/mojomast/backupussy/releases/latest)

1. Go to [Releases](https://github.com/mojomast/backupussy/releases)
2. Download `BackupUSSY-standalone-v0.1.zip`
3. Extract to any location (e.g., `C:\BackupUSSY`)
4. **That's it!** Double-click `Launch-BackupUSSY.bat`

**✅ Zero installation required**  
**✅ No Python needed**  
**✅ All dependencies bundled**  
**✅ Works immediately**

### For Developers: Source Code

```bash
git clone https://github.com/mojomast/backupussy.git
cd backupussy
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/database_init.py
```

## 📋 System Requirements

### Standalone Version (Recommended)
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4GB (8GB recommended for large archives)
- **Storage**: 20MB for application + space for archives
- **Hardware**: LTO tape drive connected via SCSI/SAS/Fibre Channel
- **Dependencies**: None! Everything is bundled

### Source Version (For Developers)
- **Python**: 3.7 or higher
- **Additional tools**: MSYS2 or GNU tar/dd

### Supported LTO Drives
- LTO-4, LTO-5, LTO-6, LTO-7, LTO-8, LTO-9
- Any Windows-compatible tape drive accessible as `\\.\TapeX`

## 🛠️ Installation

### Standalone Version (Zero-Setup)

**Download and Run:**
1. Download `BackupUSSY-standalone-v0.1.zip` from [releases](https://github.com/mojomast/backupussy/releases)
2. Extract anywhere you want
3. Double-click `Launch-BackupUSSY.bat`
4. **Done!** BackupUSSY is ready to use

**What's included:**
- ✅ BackupUSSY.exe (compiled application)
- ✅ dd.exe, tar.exe, gzip.exe (bundled tools)
- ✅ All required DLLs
- ✅ Launch scripts
- ✅ Complete documentation
- ✅ License compliance files

### Manual Installation

**1. Install System Dependencies**

**Option A: MSYS2 (Recommended)**
1. Download [MSYS2](https://www.msys2.org/)
2. Install and open MSYS2 terminal:
   ```bash
   pacman -S tar coreutils mt-st
   ```
3. Add to PATH: `C:\msys64\usr\bin`

**Option B: Manual Tools**
- Download GNU tar and dd utilities for Windows
- Place in PATH or project `bin` directory

**2. Python Environment Setup**

```bash
# Create virtual environment
python -m venv .venv

# Activate environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**3. Initialize Database**
```bash
python src/database_init.py
```

**4. Test Installation**
```bash
python src/test_runner.py
```

## 🚀 Usage

### Starting the Application

**Standalone Version:**
- Extract the downloaded zip file
- Run `BackupUSSY.exe` directly

**Source Version:**
```bash
# Activate virtual environment
.venv\Scripts\activate

# Run the application
python src/gui.py
```

### Creating Archives

1. **📂 Select Source Folder**: Browse to folder you want to archive
2. **💿 Choose Tape Device**: Select LTO device (usually `\\.\Tape0`)
3. **⚙️ Select Archive Mode**:
   - **Stream Mode**: Direct to tape (faster, no intermediate files)
   - **Cached Mode**: Create archive first (allows verification)
4. **📼 Choose Copies**: 1 or 2 tapes for redundancy
5. **🗜️ Optional**: Enable gzip compression
6. **🚀 Start Archive**: Monitor progress in real-time

### Archive Modes Explained

#### ⚡ Stream Mode
- **Process**: `tar -czf - folder/ | dd of=\\.\Tape0 bs=64k`
- **Advantages**: Faster, no disk space required
- **Best for**: Large datasets, limited disk space
- **Limitations**: No pre-verification possible

#### 💾 Cached Mode
- **Process**: Create `archive.tar.gz` → Verify → Write to tape
- **Advantages**: SHA256 verification, can retry if needed
- **Best for**: Critical data requiring verification
- **Requirements**: Additional disk space equal to archive size

### Database & Search Features

#### 🔍 **Search Interface**
- Search files across all archived tapes
- Filter by filename, path, date, size
- Export search results to CSV

#### 📂 **Tape Browser**
- Browse tape contents without extraction
- View file metadata and archive statistics
- Navigate folder structures

#### 🔧 **Recovery Manager**
- Restore individual files or entire folders
- Verify tape contents before recovery
- Progress tracking for large restorations

## 📁 Project Structure

```
backupussy/
├── 💻 APPLICATION SOURCE
│   └── src/
│       ├── gui.py               # Main GUI application
│       ├── main.py              # Entry point and dependency management
│       ├── archive_manager.py   # Archive creation logic
│       ├── tape_manager.py      # Tape operations
│       ├── logger_manager.py    # Logging system
│       ├── database_manager.py  # SQLite database
│       ├── recovery_manager.py  # File recovery
│       ├── search_interface.py  # Search functionality
│       ├── advanced_search.py   # Advanced search GUI
│       ├── tape_browser.py      # Tape content browser
│       ├── tape_library.py      # Tape library management
│       ├── database_init.py     # Database initialization
│       ├── test_runner.py       # Comprehensive test suite
│       ├── test_recovery.py     # Recovery system tests
│       └── version.py           # Version information
│
├── 📋 DOCUMENTATION
│   ├── README.md                # This comprehensive guide
│   ├── CHANGELOG.md             # Version history and changes
│   ├── CONTRIBUTING.md          # Contribution guidelines
│   └── requirements.txt         # Python dependencies
│
├── 🔧 CONFIGURATION
│   ├── .gitignore               # Git ignore rules
│   ├── LICENSE                  # MIT license
│   └── .github/workflows/       # CI/CD automation
│
└── 📊 RUNTIME DATA (created on first run)
    ├── logs/
    │   ├── archive_log.csv      # Cumulative job log
    │   └── job_*.log            # Individual job logs
    └── data/
        └── archives.db          # SQLite archive database
```

## 📊 Logging & Monitoring

### Individual Job Logs
- **Location**: `logs/job_[archive_name].log`
- **Content**: Detailed progress, timing, errors
- **Format**: Timestamped entries with severity levels

### Cumulative CSV Log
- **Location**: `logs/archive_log.csv`
- **Content**: Archive summary, statistics, checksums
- **Usage**: Excel analysis, reporting, auditing

### Database Logging
- **Archives Table**: Complete archive metadata
- **Files Table**: Individual file records with paths
- **Statistics**: Archive size, file count, compression ratios

## 🔧 Advanced Features

### Database Management
```bash
# Export database
python src/database_manager.py --export backup.sql

# Import database
python src/database_manager.py --import backup.sql

# Database statistics
python src/database_manager.py --stats
```

### Command Line Operations
```bash
# Run specific tests
python src/test_runner.py --test archive

# Recovery operations
python src/recovery_manager.py --tape Tape0 --restore /path/to/file

# Advanced search
python src/advanced_search.py --pattern "*.pdf" --date-after 2024-01-01
```

## 🐛 Troubleshooting

### Common Issues

**"Dependencies missing" Error (Source version only)**
- Run `tar --version` and `dd --version` to verify tools
- Install MSYS2 or ensure tools are in PATH
- For standalone version: Extract fresh copy from release zip

**"Tape device not accessible" Error**
- Verify tape drive power and connections
- Check Windows Device Manager for tape device
- Try different device names (`\\.\Tape1`, `\\.\Tape2`)
- Run application as Administrator

**"Archive creation failed" Error**
- Check source folder permissions
- Verify sufficient disk space (cached mode)
- Ensure folder path contains no special characters
- Review detailed logs in `logs/` directory

**Performance Issues**
- Use Stream mode for large archives
- Ensure adequate RAM (8GB+ recommended)
- Check tape drive speed compatibility
- Consider compression for repetitive data

### Diagnostic Tools

**Run Full Test Suite:**
```bash
python src/test_runner.py --verbose
```

**Check System Status (Source version):**
```bash
python src/main.py --check-deps
```

## 🏆 Features & Capabilities

### ✅ **Completed Features**
- ✅ **Standalone Application**: No Python installation required
- ✅ **Modern GUI Interface**: Complete FreeSimpleGUI application
- ✅ **Archive Modes**: Stream and cached with compression
- ✅ **Dual Tape Support**: Primary and backup copies
- ✅ **Database System**: SQLite with full indexing
- ✅ **Search & Recovery**: Advanced file search and recovery
- ✅ **Tape Management**: Browse, verify, and manage tapes
- ✅ **Comprehensive Logging**: Multiple logging levels and formats
- ✅ **Bundled Dependencies**: dd, tar, gzip included
- ✅ **Zero-Setup Distribution**: Extract and run

### 🔮 **Future Enhancements**
- 📱 Web interface for remote management
- 🏷️ Barcode label support
- 📈 Advanced reporting and analytics
- 🔄 Incremental backup support
- 🌐 Network tape library integration

## 🎓 Credits

**Created by**: Kyle Durepos

BackupUSSY represents a professional-grade solution for LTO tape archiving, developed with enterprise reliability and user-friendly operation in mind.

## 🤝 Contributing

Contributions are welcome! Please feel free to:
- Report bugs and issues
- Suggest new features
- Submit pull requests
- Improve documentation

## 📞 Support

For support, bug reports, or feature requests:
- **GitHub Issues**: [Create an issue](https://github.com/mojomast/backupussy/issues)
- **Documentation**: This README and inline code comments

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🏷️ Version History

### **v0.1** - Initial Release
- Complete standalone application (no Python required)
- Modern GUI with FreeSimpleGUI
- Stream and cached archive modes with compression
- Dual tape support for redundancy
- SQLite database with full indexing
- Advanced search and recovery capabilities
- Comprehensive logging and monitoring
- Bundled dependencies (dd, tar, gzip)
- Zero-setup distribution

---

**🎉 BackupUSSY is production-ready and fucking awesome! 🎉**

*Archive your critical data to LTO tapes with confidence and reliability.*
