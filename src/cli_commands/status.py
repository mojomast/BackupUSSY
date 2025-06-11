#!/usr/bin/env python3
"""
Status Command

Provides system status information including devices, dependencies, and current operations.
"""

import time
import threading
from typing import Dict, Any
from datetime import datetime

from .base import BaseCommand


class StatusCommand(BaseCommand):
    """Handle status command and subcommands."""
    
    def execute(self, args) -> int:
        """Execute status command."""
        try:
            component = getattr(args, 'component', None)
            watch = getattr(args, 'watch', False)
            
            if watch:
                return self._watch_status(component)
            
            if component == 'devices':
                return self._show_device_status()
            elif component == 'jobs':
                return self._show_job_status()
            elif component == 'dependencies':
                return self._show_dependency_status()
            elif component == 'tapes':
                return self._show_tape_status()
            else:
                return self._show_overall_status()
                
        except Exception as e:
            return self.handle_error(f"Failed to get status: {e}", e)
    
    def _show_overall_status(self) -> int:
        """Show overall system status."""
        print("\n=== Backupussy System Status ===")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Dependencies
        print("Dependencies:")
        dep_status = self._get_dependency_info()
        for name, info in dep_status.items():
            status_icon = "✓" if info['available'] else "✗"
            print(f"  {status_icon} {name}: {info['status']}")
        print()
        
        # Devices
        print("Tape Devices:")
        try:
            devices = self.tape_manager.detect_tape_devices()
            if devices:
                for device in devices:
                    try:
                        status = self.tape_manager.get_tape_status(device)
                        print(f"  ✓ {device}: {status['status']}")
                    except Exception as e:
                        print(f"  ⚠ {device}: Error - {e}")
            else:
                print("  ℹ No tape devices detected")
        except Exception as e:
            print(f"  ✗ Error detecting devices: {e}")
        print()
        
        # Database
        print("Database:")
        try:
            db_info = self._get_database_info()
            print(f"  ✓ Connected: {db_info['path']}")
            print(f"  ℹ Tapes: {db_info['tape_count']}")
            print(f"  ℹ Archives: {db_info['archive_count']}")
            print(f"  ℹ Files indexed: {db_info['file_count']}")
        except Exception as e:
            print(f"  ✗ Database error: {e}")
        print()
        
        # Configuration
        print("Configuration:")
        config_info = self._get_config_info()
        for key, value in config_info.items():
            print(f"  ℹ {key}: {value}")
        
        return 0
    
    def _show_device_status(self) -> int:
        """Show detailed device status."""
        print("\n=== Tape Device Status ===")
        
        try:
            devices = self.tape_manager.detect_tape_devices()
            
            if not devices:
                print("No tape devices detected.")
                print("\nTroubleshooting:")
                print("  - Ensure tape drive is connected and powered on")
                print("  - Check device drivers are installed")
                print("  - On Windows, verify device appears in Device Manager")
                print("  - Try running as administrator")
                return 1
            
            headers = ["Device", "Status", "Details", "Media"]
            rows = []
            
            for device in devices:
                try:
                    status_info = self.tape_manager.get_tape_status(device)
                    rows.append([
                        device,
                        status_info['status'],
                        status_info['details'][:30] + "..." if len(status_info['details']) > 30 else status_info['details'],
                        status_info.get('media', 'Unknown')
                    ])
                except Exception as e:
                    rows.append([device, "Error", str(e)[:30], "Unknown"])
            
            self.print_table(headers, rows)
            
        except Exception as e:
            print(f"Error getting device status: {e}")
            return 1
        
        return 0
    
    def _show_dependency_status(self) -> int:
        """Show dependency status."""
        print("\n=== Dependency Status ===")
        
        dep_info = self._get_dependency_info()
        
        headers = ["Tool", "Status", "Location", "Version Info"]
        rows = []
        
        for name, info in dep_info.items():
            status = "Available" if info['available'] else "Missing"
            location = info['path'] if info['path'] else "Not found"
            version = info.get('version', 'Unknown')
            
            rows.append([name, status, location, version])
        
        self.print_table(headers, rows)
        
        # Show installation help if any dependencies are missing
        missing = [name for name, info in dep_info.items() if not info['available']]
        if missing:
            print("\nMissing dependencies detected!")
            print("\nInstallation instructions:")
            print("  Windows (recommended): Install MSYS2")
            print("    1. Download from https://www.msys2.org/")
            print("    2. Install and run: pacman -S tar gzip")
            print("    3. Add C:\\msys64\\usr\\bin to your PATH")
            print()
            print("  Alternative: Download individual tools")
            print("    - GNU tar: https://sourceforge.net/projects/gnuwin32/files/tar/")
            print("    - dd: Usually available in Windows 10+ or download from GnuWin32")
        
        return 1 if missing else 0
    
    def _show_job_status(self) -> int:
        """Show current job status."""
        print("\n=== Job Status ===")
        
        # This would need integration with job tracking system
        # For now, show placeholder
        print("No active jobs.")
        print("\nNote: Job tracking not yet implemented in CLI.")
        print("Use the GUI interface for real-time job monitoring.")
        
        return 0
    
    def _show_tape_status(self) -> int:
        """Show tape inventory status."""
        print("\n=== Tape Inventory Status ===")
        
        try:
            tapes = self.tape_library.get_all_tapes()
            
            if not tapes:
                print("No tapes registered in inventory.")
                print("\nUse 'backupussy manage tapes add' to register tapes.")
                return 0
            
            headers = ["Label", "Device", "Status", "Archives", "Total Size", "Created"]
            rows = []
            
            for tape in tapes:
                size_str = self.format_size(tape.get('total_size_bytes', 0))
                created = tape.get('created_date', 'Unknown')
                if isinstance(created, str) and len(created) > 10:
                    created = created[:10]  # Show just date part
                
                rows.append([
                    tape['tape_label'],
                    tape['tape_device'],
                    tape['tape_status'],
                    str(tape.get('archive_count', 0)),
                    size_str,
                    created
                ])
            
            self.print_table(headers, rows)
            
            # Show summary
            total_tapes = len(tapes)
            active_tapes = len([t for t in tapes if t['tape_status'] == 'active'])
            total_archives = sum(t.get('archive_count', 0) for t in tapes)
            total_size = sum(t.get('total_size_bytes', 0) for t in tapes)
            
            print(f"\nSummary:")
            print(f"  Total tapes: {total_tapes}")
            print(f"  Active tapes: {active_tapes}")
            print(f"  Total archives: {total_archives}")
            print(f"  Total data: {self.format_size(total_size)}")
            
        except Exception as e:
            print(f"Error getting tape status: {e}")
            return 1
        
        return 0
    
    def _watch_status(self, component: str) -> int:
        """Watch status with periodic updates."""
        print(f"Watching {component or 'overall'} status... (Press Ctrl+C to stop)")
        print()
        
        try:
            while True:
                # Clear screen (works on most terminals)
                print("\033[2J\033[H", end="")
                
                if component == 'devices':
                    self._show_device_status()
                elif component == 'jobs':
                    self._show_job_status()
                elif component == 'dependencies':
                    self._show_dependency_status()
                elif component == 'tapes':
                    self._show_tape_status()
                else:
                    self._show_overall_status()
                
                print(f"\nLast update: {datetime.now().strftime('%H:%M:%S')} (Ctrl+C to stop)")
                
                time.sleep(5)  # Update every 5 seconds
                
        except KeyboardInterrupt:
            print("\nStopped watching.")
            return 0
    
    def _get_dependency_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about dependencies."""
        info = {}
        
        # Check tar
        tar_path = self.dep_manager.tar_path
        info['tar'] = {
            'available': bool(tar_path),
            'path': tar_path,
            'status': 'Available' if tar_path else 'Missing'
        }
        
        # Check dd
        dd_path = self.dep_manager.dd_path
        info['dd'] = {
            'available': bool(dd_path),
            'path': dd_path,
            'status': 'Available' if dd_path else 'Missing'
        }
        
        # Check mt (optional)
        mt_path = self.dep_manager.mt_path
        info['mt'] = {
            'available': bool(mt_path),
            'path': mt_path,
            'status': 'Available' if mt_path else 'Optional (missing)'
        }
        
        return info
    
    def _get_database_info(self) -> Dict[str, Any]:
        """Get database information."""
        try:
            # Get database stats
            stats = self.db_manager.get_database_stats()
            
            return {
                'path': str(self.db_manager.db_path),
                'tape_count': stats.get('total_tapes', 0),
                'archive_count': stats.get('total_archives', 0),
                'file_count': stats.get('total_files', 0)
            }
        except Exception as e:
            raise Exception(f"Database connection failed: {e}")
    
    def _get_config_info(self) -> Dict[str, str]:
        """Get configuration information."""
        general_config = self.config.get_section('general')
        
        return {
            'Default device': general_config.get('default_device') or 'Not set',
            'Default compression': str(general_config.get('default_compression', False)),
            'Default copies': str(general_config.get('default_copies', 1)),
            'Archive mode': general_config.get('default_mode', 'cached'),
            'Max tape capacity': f"{general_config.get('max_tape_capacity_gb', 6000)} GB"
        }

