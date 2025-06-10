# Changelog

All notable changes to BackupUSSY will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Web interface for remote management
- Barcode label support
- Advanced reporting and analytics
- Incremental backup support
- Network tape library integration

## [0.1.1] - 2025-06-10

### Fixed - Tape Device Detection
- **Enhanced Detection**: Added WMI-based tape device discovery
- **Better Fallbacks**: Improved device access testing methods
- **Permission Handling**: Better support for devices requiring elevated access
- **Debug Tools**: Added debug_tape_devices.py for troubleshooting
- **Reliability**: Always includes common tape devices (Tape0-Tape3) as options

### Technical Improvements
- Added WMI dependency for proper Windows device enumeration
- Improved error handling in tape_manager.py
- Enhanced device detection logging and feedback
- Better win32file integration for device testing

### User Experience
- Device dropdown now always shows tape options
- "Refresh Devices" button works more reliably
- Manual device selection more robust
- Better error messages for device access issues

## [0.1] - 2025-06-10

### Added - First Official Release
- **FreeSimpleGUI Interface**: Modern tabbed interface with professional design
- **Bundled Dependencies**: dd.exe, tar.exe, gzip.exe included (no external installs)
- **Zero-Setup Distribution**: Extract and run - no installation required
- **Dual Archive Modes**: 
  - Stream mode for direct tape writing
  - Cached mode with SHA256 verification
- **LTO Tape Support**: Full support for LTO-4 through LTO-9 drives
- **SQLite Database**: Complete archive indexing with metadata
- **Advanced Search**: Find files across all archived tapes
- **Tape Browser**: Browse tape contents without extraction
- **Recovery System**: Comprehensive file and folder recovery tools
- **Dual Tape Support**: Create primary and backup copies automatically
- **Compression Support**: Optional gzip compression for space efficiency
- **License Compliance**: GPL v3 compliance for bundled GNU tools
- **Comprehensive Logging**: 
  - Individual job logs with detailed progress
  - Cumulative CSV logging for analysis
  - Database logging with full metadata
- **Automated Installation**: 
  - PowerShell installer with MSYS2 integration
  - Batch file installer for basic setup
  - Dependency management and validation
- **Test Suite**: Comprehensive testing framework with validation
- **Documentation**: Complete user guide with troubleshooting

### Technical Features
- Real-time progress monitoring with live updates
- Automatic LTO device detection
- SHA256 checksum verification for data integrity
- Robust error handling and recovery mechanisms
- Export/Import capabilities for database backup
- Professional logging with multiple severity levels
- Cross-session state management
- Tape library management with statistics

### Installation & Deployment
- One-click automated installation
- MSYS2 integration for GNU tools
- Virtual environment management
- System PATH configuration
- Dependency validation and testing
- Quick launch scripts (run.bat, launch.ps1)

### System Requirements
- Windows 10/11 (64-bit)
- Python 3.7 or higher
- 4GB RAM (8GB recommended)
- LTO tape drive with Windows drivers
- 1GB+ free disk space

### Known Limitations
- Windows-only support (by design)
- No barcode labeling support (planned for future)
- No incremental backups (full archives only)
- Single-threaded archive creation
- Limited tape read-back verification

---

## Development Notes

### Architecture
- Modular design with separation of concerns
- Manager classes for different functionality areas
- SQLite database with proper schema design
- GUI framework with event-driven architecture
- Comprehensive error handling throughout

### Code Quality
- Extensive inline documentation
- Type hints where applicable
- Consistent coding standards
- Professional logging practices
- Comprehensive test coverage

### Security
- No sensitive data stored in plaintext
- Proper file permission handling
- Safe subprocess execution
- Input validation and sanitization
- Secure temporary file management

---

**This release represents a complete, production-ready LTO tape archiving solution for Windows environments.**

