#!/usr/bin/env python3
"""
Tape Device Debug Script - Helps diagnose tape device detection issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from tape_manager import TapeManager
from main import DependencyManager
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def debug_wmi_detection():
    """Debug WMI tape device detection"""
    print("\n=== WMI Tape Device Detection ===")
    try:
        import wmi
        c = wmi.WMI()
        tapes = list(c.Win32_TapeDrive())
        
        if tapes:
            print(f"Found {len(tapes)} tape devices via WMI:")
            for i, tape in enumerate(tapes):
                print(f"  Tape {i}:")
                print(f"    Name: {getattr(tape, 'Name', 'Unknown')}")
                print(f"    DeviceID: {getattr(tape, 'DeviceID', 'Unknown')}")
                print(f"    Status: {getattr(tape, 'Status', 'Unknown')}")
                print(f"    Description: {getattr(tape, 'Description', 'Unknown')}")
        else:
            print("No tape devices found via WMI")
            
    except ImportError:
        print("WMI module not available")
    except Exception as e:
        print(f"WMI detection failed: {e}")

def debug_device_access():
    """Debug direct device access"""
    print("\n=== Direct Device Access Test ===")
    
    devices_to_test = [f"\\.\\Tape{i}" for i in range(4)]
    
    for device in devices_to_test:
        print(f"\nTesting {device}:")
        
        # Test 1: Basic path existence
        try:
            os.stat(device)
            print(f"  ✓ Device path exists (os.stat)")
        except Exception as e:
            print(f"  ✗ Device path test failed: {e}")
        
        # Test 2: Win32 file handle
        try:
            import win32file
            handle = win32file.CreateFile(
                device,
                0,  # No access requested
                win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            win32file.CloseHandle(handle)
            print(f"  ✓ Device accessible via win32file")
        except ImportError:
            print(f"  ? win32file not available")
        except Exception as e:
            print(f"  ✗ win32file access failed: {e}")

def debug_backupussy_detection():
    """Debug BackupUSSY's tape detection"""
    print("\n=== BackupUSSY Tape Detection ===")
    
    try:
        dep_manager = DependencyManager()
        tape_manager = TapeManager(dep_manager)
        
        devices = tape_manager.detect_tape_devices()
        
        print(f"BackupUSSY detected {len(devices)} devices:")
        for device in devices:
            print(f"  - {device}")
            
            # Test status for each device
            status = tape_manager.get_tape_status(device)
            print(f"    Status: {status['status']} - {status['details']}")
            
    except Exception as e:
        print(f"BackupUSSY detection failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all debug tests"""
    print("🔍 BackupUSSY Tape Device Debug Tool")
    print("=====================================")
    
    debug_wmi_detection()
    debug_device_access()
    debug_backupussy_detection()
    
    print("\n=== Recommendations ===")
    print("1. Run this script as Administrator for better device access")
    print("2. Ensure tape drive has proper Windows drivers installed")
    print("3. Check Device Manager for any warning icons on tape devices")
    print("4. Try loading a tape cartridge if none is loaded")
    print("5. If \\\\.\\\\ Tape0 shows in BackupUSSY list, try using it anyway")

if __name__ == "__main__":
    main()

