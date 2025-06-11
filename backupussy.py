#!/usr/bin/env python3
"""
Backupussy CLI Entry Point

This script serves as the main entry point for running the Backupussy
command-line interface. It ensures the source directory is in the Python
path and then executes the CLI application.
"""

import sys
import os
from pathlib import Path

# Add the 'src' directory to the Python path to allow for module imports
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

try:
    from cli import main
except ImportError as e:
    print(f"Error: Could not import the CLI application. Make sure 'src/cli.py' exists. Details: {e}", file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    sys.exit(main())
