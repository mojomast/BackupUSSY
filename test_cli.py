#!/usr/bin/env python3
"""
Simple test script for the CLI interface
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cli import main

if __name__ == '__main__':
    # Test basic functionality
    print("Testing CLI with status command...")
    sys.argv = ['backupussy', 'status']
    exit_code = main()
    print(f"Exit code: {exit_code}")

