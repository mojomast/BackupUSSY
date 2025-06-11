#!/usr/bin/env python3
"""
CLI Logging Setup

Provides logging configuration for the command-line interface,
including colored output and appropriate verbosity levels.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log messages."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def __init__(self, use_color=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_color = use_color and self._supports_color()
    
    def _supports_color(self):
        """Check if the terminal supports ANSI color codes."""
        # Check if we're on Windows and if ANSI is supported
        if os.name == 'nt':
            try:
                # Try to enable ANSI support on Windows
                import colorama
                colorama.init()
                return True
            except ImportError:
                # Check if Windows 10 with ANSI support
                try:
                    from ctypes import windll, c_int, byref
                    stdout_handle = windll.kernel32.GetStdHandle(c_int(-11))
                    mode = c_int(0)
                    windll.kernel32.GetConsoleMode(c_int(stdout_handle), byref(mode))
                    windll.kernel32.SetConsoleMode(c_int(stdout_handle), c_int(mode.value | 4))
                    return True
                except:
                    return False
        
        # Unix-like systems
        return hasattr(sys.stderr, 'isatty') and sys.stderr.isatty()
    
    def format(self, record):
        """Format the log record with colors if enabled."""
        formatted = super().format(record)
        
        if self.use_color:
            level_color = self.COLORS.get(record.levelname, '')
            reset_color = self.COLORS['RESET']
            
            # Color the level name
            formatted = formatted.replace(
                record.levelname,
                f"{level_color}{record.levelname}{reset_color}",
                1  # Only replace first occurrence
            )
        
        return formatted


def setup_cli_logging(args) -> logging.Logger:
    """Set up logging for the CLI application."""
    
    # Determine log level based on verbosity
    if args.quiet:
        level = logging.ERROR
    elif args.verbose >= 2:
        level = logging.DEBUG
    elif args.verbose >= 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    
    # Create logger
    logger = logging.getLogger('backupussy.cli')
    logger.setLevel(level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Set up console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    
    # Set up formatter
    use_color = not args.no_color if hasattr(args, 'no_color') else True
    
    if args.verbose >= 1:
        # Detailed format for verbose mode
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    else:
        # Simple format for normal mode
        format_string = '%(levelname)s: %(message)s'
    
    formatter = ColoredFormatter(
        use_color=use_color,
        fmt=format_string,
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Set up file handler if specified
    if hasattr(args, 'log_file') and args.log_file:
        try:
            log_file_path = Path(args.log_file)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(logging.DEBUG)  # Always use DEBUG level for file
            
            # File format (no colors)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            logger.debug(f"Logging to file: {log_file_path}")
            
        except Exception as e:
            logger.warning(f"Failed to set up file logging: {e}")
    
    # Also set up basic logging for other modules
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[]
    )
    
    return logger


class ProgressLogger:
    """Logger that can handle progress updates without interfering with log output."""
    
    def __init__(self, logger: logging.Logger, quiet: bool = False):
        self.logger = logger
        self.quiet = quiet
        self._last_progress_line = ""
    
    def info(self, message: str):
        """Log an info message."""
        self._clear_progress()
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log a warning message."""
        self._clear_progress()
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log an error message."""
        self._clear_progress()
        self.logger.error(message)
    
    def debug(self, message: str):
        """Log a debug message."""
        self._clear_progress()
        self.logger.debug(message)
    
    def progress(self, message: str, end='\r'):
        """Display a progress message that can be overwritten."""
        if not self.quiet:
            # Clear previous progress line
            if self._last_progress_line:
                print(' ' * len(self._last_progress_line), end='\r')
            
            # Print new progress
            print(message, end=end, flush=True)
            self._last_progress_line = message if end == '\r' else ""
    
    def _clear_progress(self):
        """Clear the current progress line."""
        if self._last_progress_line:
            print(' ' * len(self._last_progress_line), end='\r')
            self._last_progress_line = ""
    
    def finish_progress(self):
        """Finish the current progress display."""
        if self._last_progress_line:
            print()  # Move to next line
            self._last_progress_line = ""

