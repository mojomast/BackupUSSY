# Changelog

All notable changes to BackupUSSY will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.4] - 2025-06-10

### Fixed - Critical Database and UI Issues
- **Database Population**: Fixed issue where database wasn't being populated when folders were stored on cassettes
- **UI Refresh**: Fixed UI not updating with new files after successful archive operations
- **Missing Database Methods**: Added `find_archive_by_name()` and `get_archive_files()` methods to database manager
- **Statistics Display**: Fixed `get_library_statistics()` method call error - now properly calls `get_database_stats()`
- **UI Update Methods**: Implemented missing `update_tape_list()`, `populate_recovery_tapes()`, and `populate_search_tapes()` methods
- **Tape Status Parameter**: Fixed `add_tape()` method to properly handle `tape_status` parameter

### Enhanced
- **Better Error Handling**: Improved error logging with full stack traces for debugging
- **Database Integration**: Enhanced archive manager integration with database operations
- **UI Responsiveness**: All tabs now properly refresh after archive operations complete
- **Statistics Updates**: Real-time statistics updates in management tab
- **User Feedback**: Better progress reporting during file indexing operations

### Technical Improvements
- Corrected method signatures in database manager
- Added comprehensive UI refresh workflow after archive completion
- Enhanced database transaction handling for archive operations
- Improved file indexing process with better error recovery
- Added proper statistics calculation and display methods

### User Experience
- Archive operations now properly populate the database with tape, archive, and file records
- UI immediately shows new archives and files after successful operations
- Statistics panel updates in real-time showing current database state
- All tabs (Archive, Recovery, Search, Management) stay synchronized
- Better feedback during long-running file indexing operations

## [0.1.3] - 2025-06-09

### Fixed
- **GUI Structure**: Corrected indentation of various helper methods in `LTOArchiveGUI` (`src/gui.py`) to their proper class-level, significantly improving code structure and maintainability.
- **GUI Logic**: Removed a duplicated code block within the `handle_import_data` method in `src/gui.py`, resolving a logical error and reducing redundancy.

### Changed
- **Core Managers**: Implemented general stability improvements and minor fixes in `src/archive_manager.py`, `src/database_manager.py`, and `src/tape_manager.py`.


### Planned
- Web interface for remote management
- Barcode label support
- Advanced reporting and analytics
- Incremental backup support
- Network tape library integration

## [0.1.2] - 2025-06-10

### Fixed - Critical Bug Fixes
- **ArchiveMode Import Error**: Fixed missing import causing "name 'ArchiveMode' is not defined" error
- **Database Method Call**: Fixed get_library_statistics to get_database_stats method call
- **Archive Job Stability**: Resolved archive creation failures due to import issues
- **GUI Reliability**: Improved application startup and archive job execution

### Technical Improvements
- Added proper ArchiveMode enum import in gui.py
- Corrected database manager method calls for statistics
- Enhanced error handling for missing imports
- Verified all manager initializations work correctly

### User Experience
- Archive jobs now start without import errors
- Statistics display correctly in management tab
- Improved application stability during operation
- Better error reporting for troubleshooting

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

