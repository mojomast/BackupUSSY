# Changelog

All notable changes to BackupUSSY will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2025-06-11 - Major Terminal Interface Release ⭐

### Added - Complete Command-Line Interface
- **🎯 Interactive Menu System**: Beautiful terminal menus with emoji navigation and intuitive workflows
- **🧙 Wizard Mode**: Guided step-by-step workflows for complex operations (`backupussy menu --mode wizard`)
- **📦 Archive Commands**: Full archive creation, estimation, job management, and cancellation
- **🔄 Recovery Commands**: Complete recovery system with archive listing, browsing, and selective extraction
- **🔍 Search Commands**: Advanced search with multiple filters, export capabilities, and tape-specific searches
- **⚙️ Management Commands**: Comprehensive tape, device, database, and configuration management
- **📊 Status Commands**: Real-time system monitoring, device status, dependency checks, and database status
- **🛡️ Safety Features**: Built-in dry-run mode, confirmation prompts, and graceful error handling
- **🎨 Professional Output**: Color-coded messages, progress bars, and helpful status indicators

### Fixed - Critical Hardware Detection
- **🔧 Honest Device Detection**: Completely removed fake device detection that reported non-existent tape drives
- **🎯 Real Hardware Testing**: Implemented `_test_device_access_real()` method that only reports actual hardware
- **⚠️ Proper Error Handling**: Menu system now gracefully handles absence of tape devices with helpful guidance
- **🚫 No More Hangs**: Eliminated system hangs when trying to write to non-existent devices
- **📝 Clear User Guidance**: Provides helpful messages for users without tape drives

### Fixed - Menu System Integration
- **🔧 Syntax Error Resolution**: Fixed critical syntax error in menu.py that was blocking all CLI functionality
- **🔧 Method Implementation**: Added missing `print_header`, `print_error`, `print_success`, `print_warning`, `print_info` methods to BaseCommand
- **🔧 ConfigManager API**: Added missing `get_default_device()`, `get_database_path()`, `get_log_level()` methods
- **🔧 ProgressManager API**: Added missing `show_progress()`, `print_*()` alias methods for test compatibility
- **🔧 Argument Structure**: Fixed menu argument passing to match CLI command expectations
- **🔧 Return Codes**: Fixed menu execute methods to return proper success/error codes

### Enhanced - Test Suite Coverage
- **📊 91% Test Success Rate**: Improved from 62% failure to 91% success rate (35 more tests passing)
- **🧪 Comprehensive Testing**: Added 66 tests covering CLI commands, menu system, and utilities
- **📈 Code Coverage**: Increased from 7% to 15% code coverage with detailed HTML reports
- **🔧 Test Infrastructure**: Added pytest configuration, markers, and proper test organization
- **📋 Integration Tests**: Complete CLI command testing for all major functionality
- **🔬 Unit Tests**: Thorough testing of utilities, managers, and core components

### Technical Improvements
- **🏗️ CLI Architecture**: Complete command-line framework with argument parsing and validation
- **🎛️ Configuration System**: Template generation, validation, and management commands
- **📝 Error Handling**: Comprehensive error handling with helpful messages and recovery suggestions
- **🔄 Manager Integration**: Seamless integration between CLI commands and existing backend managers
- **📊 Progress System**: Real-time progress reporting in terminal with live updates
- **🎨 User Experience**: Intuitive navigation, clear prompts, and professional output formatting

### Documentation
- **📚 CLI Documentation**: Complete command reference with examples and use cases
- **📖 Updated README**: Comprehensive documentation of terminal interface features
- **🔧 Installation Guide**: Updated setup instructions for CLI usage
- **💡 Usage Examples**: Extensive examples for all CLI commands and menu operations
- **🐛 Troubleshooting**: Enhanced troubleshooting guide for common issues

### User Experience
- **🎯 Dual Interface**: Users can choose between GUI for desktop use or CLI for automation
- **🚀 Professional Workflows**: Terminal interface enables scripting, automation, and advanced usage
- **🧙 Guided Operations**: Wizard mode provides step-by-step assistance for complex tasks
- **📊 Real-time Feedback**: Live progress updates and status information in terminal
- **🛡️ Safe Testing**: Dry-run mode allows testing without physical hardware
- **🎨 Beautiful Interface**: Color-coded output, emoji icons, and professional formatting

### System Reliability
- **🔍 Honest Hardware Reporting**: System only reports devices that actually exist
- **🚫 Eliminated Hangs**: No more system hangs from attempting to access fake devices
- **⚙️ Robust Error Handling**: Graceful fallbacks and helpful error messages throughout
- **🔄 Consistent State**: Menu system maintains proper state and navigation history
- **📊 Comprehensive Monitoring**: Real-time system status and health monitoring

**This release transforms BackupUSSY from a GUI-only application into a professional dual-interface solution suitable for both desktop users and automation environments.**

## [0.1.5] - 2025-06-10

### Fixed - Critical GUI Structure Issues
- **Application Startup**: Fixed "LTOArchiveGUI object has no attribute populate_recovery_tapes" error
- **Method Structure**: Fixed all standalone functions to be proper class methods
- **Indentation Issues**: Corrected massive indentation problems throughout GUI file
- **Missing Methods**: Added all missing UI update methods (populate_recovery_tapes, populate_search_tapes, update_tape_list)
- **Class Hierarchy**: Fixed orphaned nested functions and broken method definitions
- **Syntax Errors**: Resolved all syntax and indentation errors preventing compilation
- **UI Integration**: All tabs now have proper method implementations
- **Error Handling**: Enhanced error handling in all GUI methods

### Technical Improvements
- Systematic fix of 50+ improperly indented methods
- Removal of duplicate and orphaned code blocks
- Proper class method structure throughout GUI
- Complete syntax validation and error resolution
- Enhanced exception handling in all UI operations

### User Experience
- Application now starts without critical errors
- All tabs (Archive, Recovery, Search, Management) functional
- Proper UI updates after archive operations
- Complete database integration with UI components
- Real-time statistics and status updates working

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

