#!/usr/bin/env python3
"""
CLI Progress Management

Provides progress bars and status displays for long-running operations
in the command-line interface.
"""

import sys
import time
from typing import Optional, Union
from datetime import datetime, timedelta


class ProgressBar:
    """A simple progress bar for terminal display."""
    
    def __init__(self, total: int, width: int = 50, 
                 prefix: str = "Progress", suffix: str = "Complete",
                 fill: str = '█', empty: str = '-', show_percent: bool = True,
                 show_eta: bool = True, use_color: bool = True):
        """
        Initialize progress bar.
        
        Args:
            total: Total number of items to process
            width: Width of the progress bar in characters
            prefix: Text shown before the progress bar
            suffix: Text shown after the progress bar
            fill: Character used for completed portion
            empty: Character used for remaining portion
            show_percent: Whether to show percentage
            show_eta: Whether to show estimated time remaining
            use_color: Whether to use colors
        """
        self.total = total
        self.width = width
        self.prefix = prefix
        self.suffix = suffix
        self.fill = fill
        self.empty = empty
        self.show_percent = show_percent
        self.show_eta = show_eta
        self.use_color = use_color
        
        self.current = 0
        self.start_time = time.time()
        self.last_update = 0
        
        # Color codes
        self.colors = {
            'green': '\033[32m',
            'yellow': '\033[33m',
            'red': '\033[31m',
            'blue': '\033[34m',
            'reset': '\033[0m'
        } if use_color else {k: '' for k in ['green', 'yellow', 'red', 'blue', 'reset']}
    
    def update(self, current: int, custom_suffix: Optional[str] = None):
        """Update the progress bar."""
        self.current = min(current, self.total)
        now = time.time()
        
        # Throttle updates to avoid too frequent refreshes
        if now - self.last_update < 0.1 and self.current < self.total:
            return
        
        self.last_update = now
        self._display(custom_suffix)
    
    def increment(self, amount: int = 1, custom_suffix: Optional[str] = None):
        """Increment the progress by the specified amount."""
        self.update(self.current + amount, custom_suffix)
    
    def _display(self, custom_suffix: Optional[str] = None):
        """Display the current progress bar."""
        if self.total == 0:
            return
        
        percent = (self.current / self.total) * 100
        filled_length = int(self.width * self.current // self.total)
        
        # Choose color based on progress
        if percent >= 100:
            color = self.colors['green']
        elif percent >= 75:
            color = self.colors['blue']
        elif percent >= 50:
            color = self.colors['yellow']
        else:
            color = self.colors['red']
        
        # Build progress bar
        bar = color + self.fill * filled_length + self.colors['reset']
        bar += self.empty * (self.width - filled_length)
        
        # Build display string
        display_parts = [f"\r{self.prefix}: |{bar}|"]
        
        if self.show_percent:
            display_parts.append(f" {percent:5.1f}%")
        
        display_parts.append(f" ({self.current}/{self.total})")
        
        if self.show_eta and self.current > 0:
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                rate = self.current / elapsed
                if rate > 0:
                    eta_seconds = (self.total - self.current) / rate
                    eta = str(timedelta(seconds=int(eta_seconds)))
                    display_parts.append(f" ETA: {eta}")
        
        display_parts.append(f" {custom_suffix or self.suffix}")
        
        print(''.join(display_parts), end='', flush=True)
    
    def finish(self, final_message: Optional[str] = None):
        """Finish the progress bar and move to next line."""
        if final_message:
            self.update(self.total, final_message)
        else:
            self.update(self.total)
        print()  # Move to next line


class SpinnerProgress:
    """A spinner for indeterminate progress."""
    
    def __init__(self, message: str = "Processing", 
                 spinner_chars: str = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏",
                 use_color: bool = True):
        """
        Initialize spinner.
        
        Args:
            message: Message to display with spinner
            spinner_chars: Characters to cycle through for animation
            use_color: Whether to use colors
        """
        self.message = message
        self.spinner_chars = spinner_chars
        self.use_color = use_color
        
        self.current_char = 0
        self.last_update = 0
        self.active = False
        
        # Color codes
        self.color = '\033[36m' if use_color else ''  # Cyan
        self.reset = '\033[0m' if use_color else ''
    
    def update(self, message: Optional[str] = None):
        """Update the spinner."""
        now = time.time()
        
        # Throttle updates
        if now - self.last_update < 0.1:
            return
        
        self.last_update = now
        
        if message:
            self.message = message
        
        spinner_char = self.spinner_chars[self.current_char]
        self.current_char = (self.current_char + 1) % len(self.spinner_chars)
        
        display = f"\r{self.color}{spinner_char}{self.reset} {self.message}"
        print(display, end='', flush=True)
        self.active = True
    
    def finish(self, final_message: Optional[str] = None):
        """Finish the spinner and move to next line."""
        if self.active:
            if final_message:
                print(f"\r✓ {final_message}")
            else:
                print(f"\r✓ {self.message}")
            self.active = False


class ProgressManager:
    """Manages different types of progress displays."""
    
    def __init__(self, quiet: bool = False, no_color: bool = False):
        """
        Initialize progress manager.
        
        Args:
            quiet: If True, suppress all progress output
            no_color: If True, disable colored output
        """
        self.quiet = quiet
        self.use_color = not no_color
        self.current_progress = None
    
    def create_progress_bar(self, total: int, prefix: str = "Progress") -> Optional[ProgressBar]:
        """Create a new progress bar."""
        if self.quiet:
            return None
        
        self.current_progress = ProgressBar(
            total=total,
            prefix=prefix,
            use_color=self.use_color
        )
        return self.current_progress
    
    def create_spinner(self, message: str = "Processing") -> Optional[SpinnerProgress]:
        """Create a new spinner."""
        if self.quiet:
            return None
        
        self.current_progress = SpinnerProgress(
            message=message,
            use_color=self.use_color
        )
        return self.current_progress
    
    def finish_current(self, message: Optional[str] = None):
        """Finish the current progress display."""
        if self.current_progress and not self.quiet:
            self.current_progress.finish(message)
        self.current_progress = None
    
    def status(self, message: str, end: str = '\n'):
        """Display a status message."""
        if not self.quiet:
            timestamp = datetime.now().strftime('%H:%M:%S')
            if self.use_color:
                print(f"\033[90m[{timestamp}]\033[0m {message}", end=end, flush=True)
            else:
                print(f"[{timestamp}] {message}", end=end, flush=True)
    
    def success(self, message: str):
        """Display a success message."""
        if not self.quiet:
            if self.use_color:
                print(f"\033[32m✓\033[0m {message}")
            else:
                print(f"✓ {message}")
    
    def warning(self, message: str):
        """Display a warning message."""
        if not self.quiet:
            if self.use_color:
                print(f"\033[33m⚠\033[0m {message}")
            else:
                print(f"⚠ {message}")
    
    def error(self, message: str):
        """Display an error message."""
        if not self.quiet:
            if self.use_color:
                print(f"\033[31m✗\033[0m {message}", file=sys.stderr)
            else:
                print(f"✗ {message}", file=sys.stderr)
    
    def info(self, message: str):
        """Display an info message."""
        if not self.quiet:
            if self.use_color:
                print(f"\033[36mℹ\033[0m {message}")
            else:
                print(f"ℹ {message}")
    
    # Alias methods for compatibility with tests
    def show_progress(self, current: int, total: int, message: str = ""):
        """Show progress - alias for creating and updating a progress bar."""
        if not self.quiet:
            if self.current_progress is None:
                self.current_progress = self.create_progress_bar(total, "Progress")
            if self.current_progress:
                self.current_progress.update(current, message)
    
    def print_success(self, message: str):
        """Print success message - alias for success()."""
        self.success(message)
    
    def print_error(self, message: str):
        """Print error message - alias for error()."""
        self.error(message)
    
    def print_warning(self, message: str):
        """Print warning message - alias for warning()."""
        self.warning(message)
    
    def print_info(self, message: str):
        """Print info message - alias for info()."""
        self.info(message)


class FileProgress:
    """Progress display for file operations."""
    
    def __init__(self, total_bytes: int, progress_manager: ProgressManager):
        """
        Initialize file progress tracker.
        
        Args:
            total_bytes: Total number of bytes to process
            progress_manager: Progress manager instance
        """
        self.total_bytes = total_bytes
        self.progress_manager = progress_manager
        self.processed_bytes = 0
        
        self.progress_bar = progress_manager.create_progress_bar(
            total=100,  # Use percentage
            prefix="Copying"
        )
    
    def update(self, bytes_processed: int, filename: Optional[str] = None):
        """Update file progress."""
        self.processed_bytes = min(bytes_processed, self.total_bytes)
        
        if self.progress_bar:
            percent = int((self.processed_bytes / self.total_bytes) * 100) if self.total_bytes > 0 else 0
            
            # Format size display
            size_display = self._format_bytes(self.processed_bytes, self.total_bytes)
            suffix = f"{size_display}"
            
            if filename:
                suffix += f" | {filename}"
            
            self.progress_bar.update(percent, suffix)
    
    def _format_bytes(self, processed: int, total: int) -> str:
        """Format byte counts for display."""
        def format_size(size: int) -> str:
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024.0:
                    return f"{size:.1f}{unit}"
                size /= 1024.0
            return f"{size:.1f}PB"
        
        return f"{format_size(processed)} / {format_size(total)}"
    
    def finish(self, message: Optional[str] = None):
        """Finish file progress."""
        if self.progress_bar:
            self.progress_bar.finish(message or "Complete")

