# 📼 BackupUSSY - Professional LTO Tape Archive Tool

<div align="center">

![Python](https://img.shields.io/badge/python-v3.7+-blue.svg)
![Platform](https://img.shields.io/badge/platform-windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)
![Version](https://img.shields.io/badge/version-v1.0-blue.svg)

*A professional Python-based GUI tool for Windows that creates reliable archival backups to LTO tape drives*

[![Download Latest Release](https://img.shields.io/badge/Download-Latest%20Release-brightgreen?style=for-the-badge&logo=github)](https://github.com/KyleDurepos/backupussy/releases/latest)

</div>

---

## 🎯 Overview

BackupUSSY is a comprehensive LTO tape archive solution designed for Windows environments. This tool focuses on archival (non-rotating) backups with support for writing to one or two tapes per archive job, ensuring your critical data is preserved with enterprise-grade reliability.

## ✨ Key Features

### 🖥️ **Modern GUI Interface**
- **🎨 PySimpleGUI**: Intuitive and user-friendly interface
- **📊 Real-time Progress**: Live progress bars and status updates
- **🔍 Device Detection**: Automatic LTO device discovery
- **🎯 One-Click Operation**: Simple workflow for complex operations

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

### Option 1: Download from GitHub (Recommended)

[![Download Latest Release](https://img.shields.io/github/release/KyleDurepos/backupussy.svg?style=flat-square)](https://github.com/KyleDurepos/backupussy/releases/latest)

1. Go to [Releases](https://github.com/KyleDurepos/backupussy/releases)
2. Download the latest `backupussy-vX.X.zip`
3. Extract to desired location
4. Run installation:
   ```powershell
   # For complete setup (requires Administrator)
   .\install.ps1
   
   # Or basic setup (no admin required)
   install.bat
   ```
5. Launch the application:
   ```cmd
   run.bat
   ```

### Option 2: Clone from GitHub

```bash
git clone https://github.com/KyleDurepos/backupussy.git
cd backupussy
.\install.ps1
```

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11 (64-bit)
- **Python**: 3.7 or higher
- **RAM**: 4GB (8GB recommended for large archives)
- **Storage**: 1GB free space (more for cached mode)
- **Hardware**: LTO tape drive connected via SCSI/SAS/Fibre Channel

### Supported LTO Drives
- LTO-4, LTO-5, LTO-6, LTO-7, LTO-8, LTO-9
- Any Windows-compatible tape drive accessible as `\\.\TapeX`

## 🛠️ Installation

### Automated Installation (Recommended)

The automated installer handles all dependencies and configuration:

**Complete Setup** (includes MSYS2 - requires Administrator):
```powershell
# Right-click PowerShell -> "Run as Administrator"
.\install.ps1
```

**Basic Setup** (Python only - no admin required):
```cmd
install.bat
```

**The installer will:**
- ✅ Verify Python installation
- ✅ Download and install MSYS2 (if run as admin)
- ✅ Install required packages (tar, dd, mt)
- ✅ Create Python virtual environment
- ✅ Install Python dependencies
- ✅ Initialize SQLite database
- ✅ Run comprehensive functionality tests
- ✅ Configure system PATH

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

**Quick Launch:**
```cmd
run.bat
```

**Command Line:**
```bash
.venv\Scripts\python.exe src\gui.py
```

**PowerShell Launcher:**
```powershell
.\launch.ps1
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
├── 🎯 INSTALLATION & LAUNCH
│   ├── install.ps1              # Full automated installer
│   ├── install.bat              # Basic Python setup
│   ├── launch.ps1               # PowerShell launcher
│   ├── run.bat                  # Quick launch script
│   └── validate_phase2.ps1      # Installation validator
│
├── 💻 APPLICATION SOURCE
│   └── src/
│       ├── main.py              # Dependency management
│       ├── gui.py               # Main GUI application
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
│       └── test_recovery.py     # Recovery system tests
│
├── 📊 DATA & LOGS
│   ├── logs/
│   │   ├── archive_log.csv      # Cumulative job log
│   │   └── job_*.log            # Individual job logs
│   └── database/
│       └── archives.db          # SQLite archive database
│
├── 📋 DOCUMENTATION
│   ├── README.md                # This comprehensive guide
│   ├── COMPLETED.md             # Development completion status
│   ├── plan.md                  # Original development plan
│   ├── plan2.md                 # Enhanced feature plan
│   └── requirements.txt         # Python dependencies
│
└── 🔧 CONFIGURATION
    └── .venv/                   # Python virtual environment
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

**"Dependencies missing" Error**
- Run `tar --version` and `dd --version` to verify tools
- Install MSYS2 or ensure tools are in PATH
- Re-run installer with Administrator privileges

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

**Validate Installation:**
```powershell
.\validate_phase2.ps1
```

**Check System Status:**
```bash
python src/main.py --check-deps
```

## 🏆 Features & Capabilities

### ✅ **Completed Features**
- ✅ **GUI Interface**: Complete PySimpleGUI application
- ✅ **Archive Modes**: Stream and cached with compression
- ✅ **Dual Tape Support**: Primary and backup copies
- ✅ **Database System**: SQLite with full indexing
- ✅ **Search & Recovery**: Advanced file search and recovery
- ✅ **Tape Management**: Browse, verify, and manage tapes
- ✅ **Comprehensive Logging**: Multiple logging levels and formats
- ✅ **Test Coverage**: Full test suite with validation
- ✅ **Automated Installation**: One-click setup process

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
- **GitHub Issues**: [Create an issue](https://github.com/KyleDurepos/backupussy/issues)
- **Email**: support@example.com
- **Documentation**: This README and inline code comments

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🏷️ Version History

### **v1.0.0** - Initial Release
- Complete GUI application with PySimpleGUI
- Stream and cached archive modes with compression
- Dual tape support for redundancy
- SQLite database with full indexing
- Advanced search and recovery capabilities
- Comprehensive logging and monitoring
- Automated installation and setup
- Full test coverage and validation
- Professional documentation and user guides

---

**🎉 BackupUSSY is production-ready and fucking awesome! 🎉**

*Archive your critical data to LTO tapes with confidence and reliability.*
