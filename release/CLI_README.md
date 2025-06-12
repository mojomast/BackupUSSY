# Backupussy CLI - Terminal Interface

A comprehensive command-line interface for the Backupussy LTO tape backup system, providing all functionality of the GUI in a scriptable, automation-friendly format.

## Quick Start

### Installation

1. Ensure you have all dependencies installed (see [Dependencies](#dependencies))
2. Clone or download the project
3. Run the CLI from the project directory:

```bash
cd backupussy
python src/cli.py --help
```

### Basic Usage

```bash
# Check system status
python src/cli.py status

# Create an archive
python src/cli.py archive create /path/to/backup --device \\.\Tape0

# Estimate archive size
python src/cli.py archive estimate /path/to/backup

# List available archives
python src/cli.py recover list

# Search for files
python src/cli.py search "*.pdf"
```

## Features

### Core Functionality

- **Archive Management**: Create compressed/uncompressed archives with progress tracking
- **Recovery Operations**: Extract complete archives or individual files
- **Search Capabilities**: Find files across all archived tapes
- **Tape Management**: Manage tape inventory and device operations
- **System Monitoring**: Real-time status of devices, jobs, and system health

### CLI-Specific Features

- **Scriptable**: All operations can be automated through shell scripts
- **Progress Bars**: Visual progress indicators for long-running operations
- **Flexible Output**: Table, CSV, and JSON output formats
- **Configuration Files**: Persistent settings via INI or JSON config files
- **Dry Run Mode**: Preview operations without executing them
- **Detailed Logging**: Comprehensive logging with multiple verbosity levels

## Commands

### Global Options

```
--verbose, -v          Increase verbosity (use -vv for debug)
--quiet, -q            Suppress non-error output
--config FILE          Use custom configuration file
--log-file FILE        Write logs to specified file
--dry-run              Show what would be done without executing
--no-color             Disable colored output
```

### `status` - System Status

```bash
# Overall system status
backupussy status

# Check specific components
backupussy status devices      # Tape device status
backupussy status dependencies # Required tools status
backupussy status tapes        # Tape inventory
backupussy status jobs         # Current operations

# Watch for changes
backupussy status --watch
```

### `archive` - Archive Operations

```bash
# Create archive
backupussy archive create SOURCE --device DEVICE [OPTIONS]

# Options:
--name NAME            Custom archive name
--compress             Enable compression
--copies {1,2}         Number of tape copies
--mode {stream,cached} Archive mode
--no-index             Skip file indexing

# Estimate size
backupussy archive estimate SOURCE

# List and manage jobs
backupussy archive list-jobs
backupussy archive cancel [JOB_ID]
```

### `recover` - Recovery Operations

```bash
# List archives
backupussy recover list [--tape TAPE] [--after DATE]

# Browse archive contents
backupussy recover browse ARCHIVE [--path PATH]

# Extract files
backupussy recover extract ARCHIVE --output DIR [OPTIONS]

# Options:
--files PATTERNS       Extract only matching files
--verify               Verify extracted files
--preserve-structure   Maintain directory structure
```

### `search` - File Search

```bash
# Search by filename
backupussy search "filename.txt"

# Advanced search
backupussy search [OPTIONS]

# Options:
--name PATTERN         Filename pattern
--type EXTENSION       File type filter
--size SIZE            Size filter (e.g., >1MB, <100KB)
--modified-after DATE  Modified after date
--modified-before DATE Modified before date
--tape TAPE           Search specific tape
--archive ARCHIVE     Search specific archive
--export FILE         Export results to file
--format {table,csv,json} Output format
--limit N             Limit number of results
```

### `manage` - System Management

```bash
# Tape management
backupussy manage tapes list [--status STATUS]
backupussy manage tapes add --label LABEL --device DEVICE
backupussy manage tapes update LABEL [--status STATUS] [--notes NOTES]
backupussy manage tapes remove LABEL [--force]

# Device management
backupussy manage devices list
backupussy manage devices refresh

# Database operations
backupussy manage database vacuum
backupussy manage database backup OUTPUT
backupussy manage database restore BACKUP_FILE

# Statistics
backupussy manage stats [--detailed]
```

## Configuration

BackupUSSY uses a configuration file to store default settings and preferences. You can manage your configuration in a few ways:

### 1. Using the Example Template

A sample configuration file named `backupussy.conf.example` is provided in the root of the project. You can copy this file to one of the recognized locations (see below), rename it (e.g., to `backupussy.conf`), and then uncomment and modify the settings as needed.

### 2. Generating a Configuration File

You can generate a default configuration file using the CLI:

```bash
backupussy manage config generate
```

This command will create a `config.conf` file in the default user configuration directory (e.g., `~/.config/backupussy/config.conf` on Linux/macOS, or a similar path in your user's AppData directory on Windows).

Optional arguments for `generate`:
- `--path /path/to/your/config.conf`: Specify a custom path and filename for the generated configuration.
- `--force`: Overwrite the configuration file if it already exists at the target location.

### Configuration File Locations and Format

The CLI looks for configuration files in the following order, using the first one it finds:

1.  `./backupussy.conf` (in the current working directory)
2.  `./.backupussy.conf` (in the current working directory, hidden)
3.  `~/.backupussy.conf` (in the user's home directory, hidden)
4.  `~/.config/backupussy/config.conf` (standard user config directory)
5.  Windows: `%APPDATA%\Backupussy\config.conf` (User's AppData Roaming folder)
6.  Windows: `%PROGRAMDATA%\Backupussy\config.conf` (System-wide ProgramData folder)
7.  Unix-like systems: `/etc/backupussy/config.conf` (System-wide configuration)
8.  Unix-like systems: `/usr/local/etc/backupussy/config.conf` (System-wide local configuration)

Configuration files can be in INI format (recommended, like the example) or JSON format. All settings have sensible defaults, so you typically only need to specify the ones you want to change.

### Configuration Format

INI format example:

```ini
[general]
default_device = \\.\Tape0
default_compression = true
default_copies = 1
default_mode = cached

[archive]
temp_dir = C:\temp\backupussy
compression_level = 6

[logging]
level = INFO
file_rotation = true
```

JSON format example:

```json
{
  "general": {
    "default_device": "\\.\Tape0",
    "default_compression": true,
    "default_copies": 1
  },
  "archive": {
    "compression_level": 6
  }
}
```

### Environment Variables

Override configuration with environment variables:

```bash
BACKUPUSSY_GENERAL_DEFAULT_DEVICE="\\.\Tape0"
BACKUPUSSY_ARCHIVE_COMPRESSION_LEVEL=9
```
## Shell Completion (Bash/Zsh)

BackupUSSY supports command-line tab completion for Bash and Zsh shells via the `argcomplete` library. This allows you to auto-complete commands, subcommands, and options by pressing the `Tab` key.

### Activation

1.  **Ensure argcomplete is installed**:
    If you installed BackupUSSY using `pip` and the `requirements.txt` file, `argcomplete` should already be installed. If not, you can install it manually:
    ```bash
pip install argcomplete
    ```

2.  **Enable completion for your shell**:
    You need to add a line to your shell's configuration file. This typically only needs to be done once.

    *   **For Bash**:
        Add the following line to your `~/.bashrc` file:
        ```bash
eval "$(register-python-argcomplete backupussy)"
        ```
        Then, source your `.bashrc` or open a new terminal:
        ```bash
source ~/.bashrc
        ```

    *   **For Zsh**:
        Add the following line to your `~/.zshrc` file:
        ```bash
eval "$(register-python-argcomplete backupussy)"
        ```
        Then, source your `.zshrc` or open a new terminal:
        ```bash
source ~/.zshrc
        ```

    *   **Global Activation (Alternative)**:
        `argcomplete` also offers a global activation script:
        ```bash
activate-global-python-argcomplete
        ```
        You might need `sudo` for this if installing system-wide. This makes completion available for all Python scripts that use `argcomplete`. Refer to the `argcomplete` documentation for more details on global activation.

After activation, you should be able to use tab completion for `backupussy` commands. For example, typing `backupussy archive <TAB>` should show available subcommands like `create`, `estimate`, etc.

## Dependencies

### Required Tools

- **GNU tar**: For archive creation (MSYS2 recommended on Windows)
- **dd**: For tape operations (usually available on Windows 10+)
- **mt**: For tape control (optional, improves tape handling)

### Windows Installation

**Recommended: MSYS2**

1. Download and install MSYS2 from https://www.msys2.org/
2. Install required packages:
   ```bash
   pacman -S tar gzip
   ```
3. Add `C:\msys64\usr\bin` to your system PATH

**Alternative: Individual Tools**

- GNU tar: Download from GnuWin32 project
- dd: Usually available in Windows 10+ or download from GnuWin32

### Dependency Check

```bash
backupussy status dependencies
```

## Examples

### Basic Workflow

```bash
# 1. Check system status
backupussy status

# 2. Estimate archive size
backupussy archive estimate "C:\Documents"

# 3. Create compressed archive
backupussy archive create "C:\Documents" \
    --device "\\.\Tape0" \
    --compress \
    --name "Documents_Backup"

# 4. Verify the archive was created
backupussy recover list

# 5. Search for specific files
backupussy search "*.pdf" --tape "TAPE_Documents_Backup"
```

### Scripting Example

```bash
#!/bin/bash

# Automated backup script
BACKUP_SOURCE="/home/user/important_data"
TAPE_DEVICE="/dev/st0"
LOG_FILE="/var/log/backup.log"

# Check dependencies
if ! backupussy status dependencies --quiet; then
    echo "Dependencies missing, aborting backup"
    exit 1
fi

# Create backup with logging
backupussy archive create "$BACKUP_SOURCE" \
    --device "$TAPE_DEVICE" \
    --compress \
    --log-file "$LOG_FILE" \
    --verbose

echo "Backup completed, see $LOG_FILE for details"
```

### Recovery Example

```bash
# Find archives from last month
backupussy recover list --after "2025-05-01"

# Browse specific archive
backupussy recover browse "Documents_Backup_20250611_123456.tar.gz"

# Restore specific directory
backupussy recover extract "Documents_Backup_20250611_123456.tar.gz" \
    --files "project_files/*" \
    --output "/restore" \
    --verify
```

## Development Status

### Current Implementation Status

- ✅ **Foundation Framework**: Argument parsing, logging, configuration
- ✅ **Status Command**: System status and monitoring
- ✅ **Archive Command**: Basic archive creation and estimation
- 🚧 **Recovery Command**: Placeholder implementation
- 🚧 **Search Command**: Placeholder implementation
- 🚧 **Manage Command**: Placeholder implementation

### Planned Features

- **Phase 2**: Complete all command implementations
- **Phase 3**: Advanced features (batch operations, scheduling)
- **Phase 4**: Comprehensive testing and documentation

## Troubleshooting

### Common Issues

**"Missing dependencies" error**
```bash
# Check what's missing
backupussy status dependencies

# Install MSYS2 on Windows or appropriate packages on Linux
```

**"No tape devices detected"**
```bash
# Check device status
backupussy status devices

# On Windows, verify device in Device Manager
# Try running as administrator
```

**Configuration not loading**
```bash
# Check config file locations
backupussy status  # Shows current config

# Use specific config file
backupussy --config myconfig.conf status
```

### Debug Mode

```bash
# Enable debug logging
backupussy -vv status

# Save debug output to file
backupussy -vv --log-file debug.log archive estimate /path
```

## Support

For issues, feature requests, or contributions:

1. Check the main project documentation
2. Review the `plan.md` file for development roadmap
3. Enable debug logging for detailed error information
4. Include system status output when reporting issues

---

*This CLI interface is part of the Backupussy LTO tape backup system.*
*For GUI interface documentation, see the main README.*

