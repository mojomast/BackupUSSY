#!/usr/bin/env python3
"""
Base Command Class

Provides a base class for all CLI command implementations.
"""

import sys
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

from exceptions import ValidationError, BackupussyError
from pathlib import Path

if TYPE_CHECKING:
    from cli import BackupussyCLI
    from argparse import Namespace


class BaseCommand(ABC):
    """Base class for all CLI commands."""
    
    def __init__(self, managers):
        """
        Initialize command with managers dictionary.
        
        Args:
            managers: Dictionary of manager instances
        """
        self.managers = managers
        self.logger = managers.get('logger')
        self.config = managers.get('config_manager')
        self.progress = managers.get('progress_manager')
        
        # Backend managers (will be available after initialization)
        self.dep_manager = managers.get('dep_manager')
        self.archive_manager = managers.get('archive_manager')
        self.tape_manager = managers.get('tape_manager')
        self.db_manager = managers.get('db_manager')
        self.recovery_manager = managers.get('recovery_manager')
        self.search_interface = managers.get('search_interface')
        self.tape_library = managers.get('tape_library')
    
    @abstractmethod
    def execute(self, args) -> int:
        """
        Execute the command.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        pass
    
    def validate_path(self, path: str, must_exist: bool = True, must_be_dir: bool = False) -> Path:
        """
        Validate and return a Path object.
        
        Args:
            path: Path string to validate
            must_exist: Whether the path must exist
            must_be_dir: Whether the path must be a directory
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If validation fails
        """
        path_obj = Path(path).resolve()
        
        if must_exist and not path_obj.exists():
            raise ValidationError(f"Path does not exist: {path}")
        
        if must_exist and must_be_dir and not path_obj.is_dir():
            raise ValidationError(f"Path is not a directory: {path}")
        
        return path_obj
    
    def confirm_action(self, args: 'Namespace', message: str, default: bool = False) -> bool:
        """
        Ask user for confirmation.
        
        Args:
            args: Parsed command line arguments (e.g., from argparse). Expected to 
                  have a 'force' attribute (boolean).
            message: Confirmation message
            default: Default response if user just presses Enter
            
        Returns:
            True if user confirms, False otherwise
        """
        if getattr(args, 'force', False):
            self.logger.debug("Confirmation bypassed due to --force flag.")
            return True
        
        default_str = "Y/n" if default else "y/N"
        prompt = f"{message} [{default_str}]: "
        
        try:
            response = input(prompt).strip().lower()
        except EOFError:
            self.logger.warning(f"EOFError during confirmation for '{message}'. Assuming default: {default}.")
            return default
        except KeyboardInterrupt:
            self.logger.warning(f"User interrupted confirmation for '{message}'. Assuming 'no'.")
            # Add a newline to make the terminal output cleaner after ^C
            # Prefer sys.stderr for prompts if stdout might be redirected, but input() uses stdout for prompt.
            # For simplicity here, just ensuring a newline if possible.
            try:
                sys.stdout.write('\n')
                sys.stdout.flush()
            except BlockingIOError: # pragma: no cover
                pass # Non-blocking stdout, can't guarantee flush
            return False # Typically, interrupt means cancel/no
            
        if not response:
            return default
        
        return response in ['y', 'yes', 'true', '1']
    
    def format_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def format_duration(self, seconds: float) -> str:
        """
        Format duration in human-readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    def handle_error(self, message: str, exception: Optional[Exception] = None, exit_code: int = 1) -> int:
        """
        Handle and report errors consistently.
        
        Args:
            message: Error message to display
            exception: Optional exception that caused the error
            exit_code: Exit code to return
            
        Returns:
            The provided exit code
        """
        self.logger.error(message)
        
        if exception and self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"Exception details: {exception}", exc_info=True)
        
        if self.progress:
            self.progress.error(message)
        
        return exit_code
    
    def print_table(self, headers, rows, max_col_width: int = 50) -> None:
        """
        Print a formatted table.
        
        Args:
            headers: Column headers
            rows: Table rows
            max_col_width: Maximum column width
        """
        if not rows:
            print("No data to display.")
            return
        
        # Calculate column widths
        col_widths = [len(header) for header in headers]
        
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], min(len(str(cell)), max_col_width))
        
        # Print header
        header_row = " | ".join(header.ljust(col_widths[i]) for i, header in enumerate(headers))
        print(header_row)
        print("-" * len(header_row))
        
        # Print rows
        for row in rows:
            formatted_cells = []
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    cell_str = str(cell)
                    if len(cell_str) > max_col_width:
                        cell_str = cell_str[:max_col_width-3] + "..."
                    formatted_cells.append(cell_str.ljust(col_widths[i]))
                else:
                    formatted_cells.append(str(cell))
            
            print(" | ".join(formatted_cells))
    
    def print_header(self, message: str):
        """Print a header message."""
        if self.progress:
            # Display header with visual emphasis
            print("\n" + "=" * len(message))
            print(message)
            print("=" * len(message))
        else:
            print(f"\n{message}")
    
    def print_success(self, message: str):
        """Print a success message."""
        if self.progress:
            self.progress.success(message)
        else:
            print(f"✓ {message}")
    
    def print_error(self, message: str):
        """Print an error message."""
        if self.progress:
            self.progress.error(message)
        else:
            print(f"✗ {message}", file=sys.stderr)
    
    def print_warning(self, message: str):
        """Print a warning message."""
        if self.progress:
            self.progress.warning(message)
        else:
            print(f"⚠ {message}")
    
    def print_info(self, message: str):
        """Print an info message."""
        if self.progress:
            self.progress.info(message)
        else:
            print(f"ℹ {message}")
    
    def get_device_from_args(self, args) -> str:
        """
        Get tape device from args or config.
        
        Args:
            args: Command line arguments
            
        Returns:
            Device path
            
        Raises:
            ValidationError: If no device specified
        """
        device = getattr(args, 'device', None)
        
        if not device:
            device = self.config.get('general', 'default_device')
        
        if not device:
            raise ValidationError("No tape device specified. Use --device option or set default_device in config.")
        
        return device
    
    def dry_run_check(self, args, action_description: str) -> bool:
        """
        Check if this is a dry run and display what would be done.
        
        Args:
            args: Command line arguments
            action_description: Description of the action that would be performed
            
        Returns:
            True if this is a dry run (should skip actual execution)
        """
        if getattr(args, 'dry_run', False):
            self.progress.info(f"DRY RUN: Would {action_description}")
            return True
        return False

