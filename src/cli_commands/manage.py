#!/usr/bin/env python3
"""
Manage Command

Handles tape and system management operations including tape inventory,
device management, database operations, and system statistics.
"""

import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from .base import BaseCommand
from exceptions import ValidationError, ManagementError


class ManageCommand(BaseCommand):
    """Handle manage command and subcommands."""
    
    def execute(self, args) -> int:
        """Execute manage command."""
        action = getattr(args, 'manage_action', None)
        
        if not action:
            raise ValidationError("No management action specified. Use 'manage --help' for options.")
        
        action_map = {
            'tapes': self._handle_tape_management,
            'devices': self._handle_device_management,
            'database': self._handle_database_management,
            'stats': self._show_statistics,
            'config': self._handle_config_management
        }
        
        if action in action_map:
            return action_map[action](args)
        else:
            raise ValidationError(f"Unknown management action: {action}")
    
    def _handle_tape_management(self, args) -> int:
        """Handle tape-related management operations."""
        tape_action = getattr(args, 'tapes_action', None)
        
        if not tape_action:
            raise ValidationError("No tape action specified. Use 'manage tapes --help' for options.")
        
        tape_actions = {
            'list': self._list_tapes,
            'add': self._add_tape,
            'update': self._update_tape,
            'remove': self._remove_tape
        }
        
        if tape_action in tape_actions:
            return tape_actions[tape_action](args)
        else:
            raise ValidationError(f"Unknown tape action: {tape_action}")
    
    def _list_tapes(self, args) -> int:
        """List all tapes in the inventory."""
        status_filter = getattr(args, 'status', None)
        
        self.progress.status("Fetching tape inventory...")
        
        try:
            tapes = self.tape_library.get_all_tapes()
            
            if status_filter:
                tapes = [t for t in tapes if t.get('tape_status', '').lower() == status_filter.lower()]
                self.progress.info(f"Filtered by status: {status_filter}")
            
            if not tapes:
                self.progress.info("No tapes found matching criteria.")
                return 0
            
            self.progress.success(f"Found {len(tapes)} tapes.")
            
            # Display tapes in table format
            headers = ["Label", "Device", "Status", "Archives", "Total Size", "Created", "Notes"]
            rows = []
            
            for tape in tapes:
                size_str = self.format_size(tape.get('total_size_bytes', 0))
                created = tape.get('created_date', 'Unknown')
                if isinstance(created, str) and len(created) > 10:
                    created = created[:10]  # Show just date part
                
                notes = tape.get('notes', '')[:30]  # Truncate long notes
                if len(tape.get('notes', '')) > 30:
                    notes += "..."
                
                rows.append([
                    tape.get('tape_label', ''),
                    tape.get('tape_device', ''),
                    tape.get('tape_status', ''),
                    str(tape.get('archive_count', 0)),
                    size_str,
                    created,
                    notes
                ])
            
            self.print_table(headers, rows)
            
            # Show summary statistics
            total_size = sum(t.get('total_size_bytes', 0) for t in tapes)
            active_count = len([t for t in tapes if t.get('tape_status') == 'active'])
            total_archives = sum(t.get('archive_count', 0) for t in tapes)
            
            print(f"\nSummary:")
            print(f"  Total tapes: {len(tapes)}")
            print(f"  Active tapes: {active_count}")
            print(f"  Total archives: {total_archives}")
            print(f"  Total data: {self.format_size(total_size)}")
            
            return 0
            
        except Exception as e:
            return self.handle_error(f"Failed to list tapes: {e}", e)
    
    def _add_tape(self, args) -> int:
        """Add a new tape to the inventory."""
        label = getattr(args, 'label')
        device = getattr(args, 'device')
        notes = getattr(args, 'notes', '')
        
        if not label or not device:
            raise ValidationError("Both --label and --device are required to add a tape.")
        
        # Validate device exists (if possible)
        try:
            if self.tape_manager:
                available_devices = self.tape_manager.detect_tape_devices()
                if available_devices and device not in available_devices:
                    self.progress.warning(f"Device {device} not detected. Adding anyway...")
        except Exception:
            # Device detection failed, but continue anyway
            pass
        
        self.progress.status(f"Adding tape '{label}' with device '{device}'...")
        
        try:
            # Check if tape already exists
            existing_tape = self.db_manager.find_tape_by_label(label)
            if existing_tape:
                raise ValidationError(f"Tape with label '{label}' already exists.")
            
            # Add tape to database
            tape_id = self.tape_library.add_tape(
                label=label,
                device=device,
                status='active',
                notes=notes
            )
            
            self.progress.success(f"Successfully added tape '{label}' (ID: {tape_id}).")
            
            # Show the new tape details
            print(f"\nTape Details:")
            print(f"  Label: {label}")
            print(f"  Device: {device}")
            print(f"  Status: active")
            print(f"  Database ID: {tape_id}")
            if notes:
                print(f"  Notes: {notes}")
            
            return 0
            
        except Exception as e:
            return self.handle_error(f"Failed to add tape: {e}", e)
    
    def _update_tape(self, args) -> int:
        """Update tape information."""
        label = getattr(args, 'label')
        new_status = getattr(args, 'status', None)
        new_notes = getattr(args, 'notes', None)
        
        if not label:
            raise ValidationError("Tape label is required for update.")
        
        if not new_status and new_notes is None:
            raise ValidationError("At least one of --status or --notes must be provided.")
        
        self.progress.status(f"Updating tape '{label}'...")
        
        try:
            # Find the tape
            tape = self.db_manager.find_tape_by_label(label)
            if not tape:
                raise ValidationError(f"Tape with label '{label}' not found.")
            
            # Validate new status if provided
            valid_statuses = ['active', 'full', 'damaged', 'retired']
            if new_status and new_status not in valid_statuses:
                raise ValidationError(f"Invalid status '{new_status}'. Valid options: {', '.join(valid_statuses)}")
            
            # Update the tape
            updates = {}
            if new_status:
                updates['tape_status'] = new_status
            if new_notes is not None:
                updates['notes'] = new_notes
            
            self.tape_library.update_tape(tape['tape_id'], **updates)
            
            self.progress.success(f"Successfully updated tape '{label}'.")
            
            # Show updated tape details
            updated_tape = self.db_manager.find_tape_by_label(label)
            print(f"\nUpdated Tape Details:")
            print(f"  Label: {updated_tape['tape_label']}")
            print(f"  Device: {updated_tape['tape_device']}")
            print(f"  Status: {updated_tape['tape_status']}")
            print(f"  Last Modified: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            if updated_tape.get('notes'):
                print(f"  Notes: {updated_tape['notes']}")
            
            return 0
            
        except Exception as e:
            return self.handle_error(f"Failed to update tape: {e}", e)
    
    def _remove_tape(self, args) -> int:
        """Remove a tape from the inventory."""
        label = getattr(args, 'label')
        force = getattr(args, 'force', False)
        
        if not label:
            raise ValidationError("Tape label is required for removal.")
        
        self.progress.status(f"Finding tape '{label}'...")
        
        try:
            # Find the tape
            tape = self.db_manager.find_tape_by_label(label)
            if not tape:
                raise ValidationError(f"Tape with label '{label}' not found.")
            
            # Check if tape has archives
            archives = self.db_manager.get_all_archives(tape_id=tape['tape_id'])
            
            if archives and not force:
                print(f"\nWarning: Tape '{label}' contains {len(archives)} archive(s):")
                for archive in archives[:5]:  # Show first 5
                    print(f"  - {archive['archive_name']} ({archive['archive_date']})")
                if len(archives) > 5:
                    print(f"  ... and {len(archives) - 5} more")
                
                if not self.confirm_action("This will permanently remove the tape and all its archive records. Continue?", default=False):
                    self.progress.info("Tape removal cancelled.")
                    return 0
            
            # Remove the tape
            self.tape_library.remove_tape(tape['tape_id'])
            
            self.progress.success(f"Successfully removed tape '{label}' and {len(archives)} associated archive record(s).")
            
            return 0
            
        except Exception as e:
            return self.handle_error(f"Failed to remove tape: {e}", e)
    
    def _handle_device_management(self, args) -> int:
        """Handle device-related management operations."""
        device_action = getattr(args, 'devices_action', None)
        
        if not device_action:
            raise ValidationError("No device action specified. Use 'manage devices --help' for options.")
        
        if device_action == 'list':
            return self._list_devices()
        elif device_action == 'refresh':
            return self._refresh_devices()
        else:
            raise ValidationError(f"Unknown device action: {device_action}")
    
    def _list_devices(self) -> int:
        """List available tape devices."""
        self.progress.status("Detecting tape devices...")
        
        try:
            devices = self.tape_manager.detect_tape_devices()
            
            if not devices:
                self.progress.warning("No tape devices detected.")
                print("\nTroubleshooting tips:")
                print("  - Ensure tape drive is connected and powered on")
                print("  - Check that device drivers are properly installed")
                print("  - On Windows, verify device appears in Device Manager")
                print("  - Try running as administrator")
                print("  - Check cable connections")
                return 1
            
            self.progress.success(f"Found {len(devices)} tape device(s).")
            
            headers = ["Device Path", "Status", "Details", "Media Type"]
            rows = []
            
            for device in devices:
                try:
                    status_info = self.tape_manager.get_tape_status(device)
                    status = status_info.get('status', 'Unknown')
                    details = status_info.get('details', 'No details available')[:40]
                    media = status_info.get('media', 'Unknown')
                    
                    rows.append([device, status, details, media])
                except Exception as e:
                    rows.append([device, "Error", str(e)[:40], "Unknown"])
            
            self.print_table(headers, rows)
            
            # Show configuration hint
            current_default = self.config.get('general', 'default_device')
            if current_default:
                print(f"\nCurrent default device: {current_default}")
            else:
                print(f"\nTo set a default device, add to your config file:")
                print(f"  [general]")
                print(f"  default_device = {devices[0]}")
            
            return 0
            
        except Exception as e:
            return self.handle_error(f"Failed to list devices: {e}", e)
    
    def _refresh_devices(self) -> int:
        """Refresh device detection."""
        self.progress.status("Refreshing device detection...")
        
        try:
            # Force re-detection
            self.tape_manager.__init__(self.dep_manager)  # Reinitialize
            devices = self.tape_manager.detect_tape_devices()
            
            self.progress.success(f"Device detection refreshed. Found {len(devices)} device(s).")
            
            if devices:
                print("\nDetected devices:")
                for device in devices:
                    print(f"  - {device}")
            else:
                print("\nNo devices detected after refresh.")
            
            return 0
            
        except Exception as e:
            return self.handle_error(f"Failed to refresh devices: {e}", e)
    
    def _handle_database_management(self, args) -> int:
        """Handle database-related management operations."""
        db_action = getattr(args, 'database_action', None)
        
        if not db_action:
            raise ValidationError("No database action specified. Use 'manage database --help' for options.")
        
        db_actions = {
            'vacuum': self._vacuum_database,
            'backup': self._backup_database,
            'restore': self._restore_database
        }
        
        if db_action in db_actions:
            return db_actions[db_action](args)
        else:
            raise ValidationError(f"Unknown database action: {db_action}")
    
    def _vacuum_database(self, args) -> int:
        """Vacuum the database to optimize performance."""
        self.progress.status("Starting database vacuum operation...")
        
        try:
            # Get database size before vacuum
            db_path = Path(self.db_manager.db_path)
            size_before = db_path.stat().st_size if db_path.exists() else 0
            
            # Perform vacuum
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
            
            # Get size after vacuum
            size_after = db_path.stat().st_size if db_path.exists() else 0
            size_saved = size_before - size_after
            
            self.progress.success("Database vacuum completed successfully.")
            
            print(f"\nVacuum Results:")
            print(f"  Size before: {self.format_size(size_before)}")
            print(f"  Size after: {self.format_size(size_after)}")
            if size_saved > 0:
                print(f"  Space saved: {self.format_size(size_saved)}")
            else:
                print(f"  No space saved (database was already optimized)")
            
            return 0
            
        except Exception as e:
            return self.handle_error(f"Database vacuum failed: {e}", e)
    
    def _backup_database(self, args) -> int:
        """Create a backup of the database."""
        output_path = getattr(args, 'output')
        
        if not output_path:
            raise ValidationError("Output path is required for database backup.")
        
        output_file = Path(output_path)
        
        # Create output directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.progress.status(f"Creating database backup at {output_file}...")
        
        try:
            db_path = Path(self.db_manager.db_path)
            
            if not db_path.exists():
                raise ManagementError("Database file does not exist.")
            
            # Copy the database file
            shutil.copy2(db_path, output_file)
            
            # Verify the backup
            if output_file.exists():
                original_size = db_path.stat().st_size
                backup_size = output_file.stat().st_size
                
                if original_size == backup_size:
                    self.progress.success(f"Database backup created successfully.")
                    
                    print(f"\nBackup Details:")
                    print(f"  Original: {db_path} ({self.format_size(original_size)})")
                    print(f"  Backup: {output_file} ({self.format_size(backup_size)})")
                    print(f"  Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    return 0
                else:
                    raise ManagementError("Backup verification failed: size mismatch.")
            else:
                raise ManagementError("Backup file was not created.")
            
        except Exception as e:
            return self.handle_error(f"Database backup failed: {e}", e)
    
    def _restore_database(self, args) -> int:
        """Restore database from backup."""
        backup_file = getattr(args, 'backup_file')
        
        if not backup_file:
            raise ValidationError("Backup file path is required for database restore.")
        
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            raise ValidationError(f"Backup file does not exist: {backup_file}")
        
        current_db = Path(self.db_manager.db_path)
        
        # Create backup of current database if it exists
        if current_db.exists():
            backup_current = current_db.with_suffix('.bak')
            if not self.confirm_action(f"This will replace the current database. A backup will be saved as {backup_current}. Continue?", default=False):
                self.progress.info("Database restore cancelled.")
                return 0
            
            shutil.copy2(current_db, backup_current)
            self.progress.info(f"Current database backed up to {backup_current}")
        
        self.progress.status(f"Restoring database from {backup_path}...")
        
        try:
            # Restore the database
            shutil.copy2(backup_path, current_db)
            
            # Verify the restore
            if current_db.exists():
                # Test database connectivity
                try:
                    with sqlite3.connect(str(current_db)) as conn:
                        conn.execute("SELECT COUNT(*) FROM sqlite_master")
                    
                    self.progress.success("Database restored successfully.")
                    
                    print(f"\nRestore Details:")
                    print(f"  Backup source: {backup_path}")
                    print(f"  Restored to: {current_db}")
                    print(f"  Size: {self.format_size(current_db.stat().st_size)}")
                    print(f"  Restored: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    return 0
                    
                except sqlite3.Error as e:
                    raise ManagementError(f"Restored database appears to be corrupt: {e}")
            else:
                raise ManagementError("Database restore failed: file was not created.")
            
        except Exception as e:
            return self.handle_error(f"Database restore failed: {e}", e)
    
    def _show_statistics(self, args) -> int:
        """Show comprehensive system statistics."""
        detailed = getattr(args, 'detailed', False)
        
        self.progress.status("Gathering system statistics...")
        
        try:
            # Get database statistics
            stats = self.db_manager.get_database_stats()
            
            # Get tape information
            tapes = self.tape_library.get_all_tapes()
            
            # Get device information
            try:
                devices = self.tape_manager.detect_tape_devices()
            except:
                devices = []
            
            self.progress.success("Statistics compiled successfully.")
            
            print(f"\n=== System Statistics ===")
            print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Database stats
            print(f"\nDatabase:")
            print(f"  Location: {self.db_manager.db_path}")
            print(f"  Size: {self.format_size(Path(self.db_manager.db_path).stat().st_size)}")
            print(f"  Total tapes: {stats.get('total_tapes', 0)}")
            print(f"  Total archives: {stats.get('total_archives', 0)}")
            print(f"  Total files indexed: {stats.get('total_files', 0):,}")
            
            # Tape statistics
            if tapes:
                print(f"\nTape Library:")
                active_tapes = [t for t in tapes if t.get('tape_status') == 'active']
                full_tapes = [t for t in tapes if t.get('tape_status') == 'full']
                damaged_tapes = [t for t in tapes if t.get('tape_status') == 'damaged']
                retired_tapes = [t for t in tapes if t.get('tape_status') == 'retired']
                
                total_size = sum(t.get('total_size_bytes', 0) for t in tapes)
                total_archives = sum(t.get('archive_count', 0) for t in tapes)
                
                print(f"  Active tapes: {len(active_tapes)}")
                print(f"  Full tapes: {len(full_tapes)}")
                print(f"  Damaged tapes: {len(damaged_tapes)}")
                print(f"  Retired tapes: {len(retired_tapes)}")
                print(f"  Total data stored: {self.format_size(total_size)}")
                print(f"  Total archives: {total_archives}")
                
                if detailed and active_tapes:
                    print(f"\n  Active Tape Details:")
                    for tape in active_tapes:
                        size = self.format_size(tape.get('total_size_bytes', 0))
                        archives = tape.get('archive_count', 0)
                        print(f"    {tape['tape_label']}: {archives} archives, {size}")
            
            # Device information
            print(f"\nDevices:")
            print(f"  Detected tape devices: {len(devices)}")
            if devices:
                for device in devices:
                    print(f"    - {device}")
            else:
                print(f"    No devices currently detected")
            
            # Configuration info
            print(f"\nConfiguration:")
            config_general = self.config.get_section('general')
            print(f"  Default device: {config_general.get('default_device') or 'Not set'}")
            print(f"  Default compression: {config_general.get('default_compression', False)}")
            print(f"  Max tape capacity: {config_general.get('max_tape_capacity_gb', 6000)} GB")
            
            if detailed:
                # Detailed breakdown by tape status
                print(f"\n=== Detailed Breakdown ===")
                for status in ['active', 'full', 'damaged', 'retired']:
                    status_tapes = [t for t in tapes if t.get('tape_status') == status]
                    if status_tapes:
                        print(f"\n{status.title()} Tapes ({len(status_tapes)}):")
                        for tape in status_tapes:
                            size = self.format_size(tape.get('total_size_bytes', 0))
                            print(f"  {tape['tape_label']}: {tape.get('archive_count', 0)} archives, {size}")
            
            return 0
            
        except Exception as e:
            return self.handle_error(f"Failed to generate statistics: {e}", e)

    def _handle_config_management(self, args) -> int:
        """Handle configuration management operations."""
        config_action = getattr(args, 'config_action', None)

        if not config_action:
            raise ValidationError("No config action specified. Use 'manage config --help' for options.")

        config_actions = {
            'generate': self._generate_config_file
        }

        if config_action in config_actions:
            return config_actions[config_action](args)
        else:
            raise ValidationError(f"Unknown config action: {config_action}")

    def _generate_config_file(self, args) -> int:
        """Generate a sample configuration file."""
        custom_path_str = getattr(args, 'path', None)
        force_overwrite = getattr(args, 'force', False)

        try:
            if custom_path_str:
                target_path = Path(custom_path_str).resolve()
            else:
                # Default path from ConfigManager's save method (user config dir)
                # We let the save method determine the default path.
                target_path = Path.home() / '.config' / 'backupussy' / 'config.conf'
                # Ensure parent directory exists for default path
                target_path.parent.mkdir(parents=True, exist_ok=True)

            if target_path.exists() and not force_overwrite:
                self.progress.warning(f"Configuration file already exists at {target_path}")
                self.progress.info("Use --force to overwrite.")
                return 1 # Indicate non-fatal error/user cancellation
            
            # The ConfigManager.save() method will save the current config state.
            # If we want a *sample* config, we should use the _create_sample_ini_config logic.
            # For now, let's assume self.config is already loaded with defaults if no user file was found,
            # or we can re-initialize a temporary ConfigManager for pristine defaults.
            
            # To ensure a *sample* (default) config is generated, we'll use the internal method
            # of ConfigManager that _create_sample_ini_config uses, or replicate its content.
            # The ConfigManager's save() method saves the *current* config, which might be merged
            # with an existing file. For a true 'generate sample', we need the raw default.

            # Re-instantiate a ConfigManager to get default config or use the _create_sample_ini_config logic
            # For simplicity, we'll directly use the logic from _create_sample_ini_config
            # This avoids issues if the main self.config has been modified or loaded from an existing file.
            
            sample_content = """
# Backupussy Configuration File
# This file contains configuration options for the Backupussy LTO backup system.
# All options have sensible defaults, so you only need to uncomment and modify
# the settings you want to change.

[general]
# Default tape device to use when none specified
# default_device = /dev/st0

# Enable compression by default
# default_compression = true

# Default number of tape copies
# default_copies = 1

# Default archive mode (stream or cached)
# default_mode = cached

# Maximum tape capacity in GB (LTO-7 = 6000)
# max_tape_capacity_gb = 6000

# Progress update interval in seconds
# progress_update_interval = 0.1

[database]
# Database file path (relative to application directory or absolute)
# path = data/backupussy.db

# How often to backup the database (days)
# backup_interval_days = 7

# Whether to vacuum database on startup
# vacuum_on_startup = false

[logging]
# Logging level (DEBUG, INFO, WARNING, ERROR)
# level = INFO

# Enable log file rotation
# file_rotation = true

# Maximum number of log files to keep
# max_log_files = 10

# Maximum log file size in MB
# max_log_size_mb = 50

[archive]
# Temporary directory for archive creation (empty = system temp)
# temp_dir = 

# Verify checksums during archive creation
# verify_checksums = true

# Index files in database by default
# index_files_by_default = true

# Compression level (1-9, 6 is good balance)
# compression_level = 6

[recovery]
# Verify recovered files by default
# verify_by_default = true

# Preserve directory structure by default
# preserve_structure_by_default = true

# Buffer size for recovery operations (MB)
# buffer_size_mb = 64

[search]
# Default search result limit
# default_limit = 1000

# Case sensitive searches by default
# case_sensitive = false

# Use regular expressions by default
# use_regex = false
""".strip()

            with open(target_path, 'w') as f:
                f.write(sample_content)

            self.progress.success(f"Sample configuration file generated at: {target_path}")
            return 0

        except IOError as e:
            return self.handle_error(f"Failed to write configuration file to {target_path}: {e}", e)
        except Exception as e:
            return self.handle_error(f"An unexpected error occurred while generating config: {e}", e)

