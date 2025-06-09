#!/usr/bin/env python3
"""
Tape Manager - Handles LTO tape device interaction using dd and mt.
"""

import os
import subprocess
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

class TapeManager:
    """Manages LTO tape device operations."""
    
    def __init__(self, dependency_manager):
        self.dep_manager = dependency_manager
        self.default_device = "\\.\\Tape0"
        self.block_size = 65536  # 64KB blocks
    
    def detect_tape_devices(self):
        """Detect available tape devices."""
        devices = []
        
        # Check common Windows tape device names
        for i in range(8):  # Check Tape0 through Tape7
            device = f"\\.\\Tape{i}"
            if self._test_device_access(device):
                devices.append(device)
        
        logger.info(f"Found {len(devices)} tape devices: {devices}")
        return devices
    
    def _test_device_access(self, device):
        """Test if a tape device is accessible."""
        try:
            # Try to open the device for reading (non-destructive test)
            with open(device, 'rb') as f:
                # Just opening is enough to test access
                pass
            return True
        except (OSError, PermissionError):
            return False
    
    def get_tape_status(self, device=None):
        """Get status information about the tape."""
        if device is None:
            device = self.default_device
        
        # Try to get tape status using mt if available
        if self.dep_manager.mt_path:
            try:
                result = subprocess.run(
                    [self.dep_manager.mt_path, '-f', device, 'status'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    return {
                        'status': 'ready',
                        'details': result.stdout.strip()
                    }
                else:
                    return {
                        'status': 'error',
                        'details': result.stderr.strip()
                    }
            except Exception as e:
                logger.warning(f"Error getting tape status: {e}")
        
        # Fallback: simple device accessibility test
        if self._test_device_access(device):
            return {'status': 'accessible', 'details': 'Device is accessible'}
        else:
            return {'status': 'not_accessible', 'details': 'Device not accessible'}
    
    def rewind_tape(self, device=None):
        """Rewind the tape to the beginning."""
        if device is None:
            device = self.default_device
        
        if not self.dep_manager.mt_path:
            logger.warning("mt command not available - cannot rewind tape")
            return False
        
        try:
            logger.info(f"Rewinding tape {device}...")
            result = subprocess.run(
                [self.dep_manager.mt_path, '-f', device, 'rewind'],
                capture_output=True,
                text=True,
                timeout=60  # Rewind can take time
            )
            
            if result.returncode == 0:
                logger.info("Tape rewound successfully")
                return True
            else:
                logger.error(f"Failed to rewind tape: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Tape rewind timed out")
            return False
        except Exception as e:
            logger.error(f"Error rewinding tape: {e}")
            return False
    
    def write_archive_to_tape(self, archive_path, device=None, progress_callback=None):
        """Write an archive file to tape using dd."""
        if device is None:
            device = self.default_device
        
        if not self.dep_manager.dd_path:
            raise RuntimeError("dd executable not available")
        
        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"Archive file not found: {archive_path}")
        
        # Get file size for progress calculation
        file_size = os.path.getsize(archive_path)
        logger.info(f"Writing {file_size} bytes to tape {device}")
        
        # Build dd command
        cmd = [
            self.dep_manager.dd_path,
            f'if={archive_path}',
            f'of={device}',
            f'bs={self.block_size}',
            'status=progress'  # Show progress
        ]
        
        try:
            # Execute dd command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            
            bytes_written = 0
            
            # Monitor progress
            while True:
                # dd outputs progress to stderr
                output = process.stderr.readline()
                
                if output == '' and process.poll() is not None:
                    break
                
                if output and progress_callback:
                    # Parse dd progress output
                    if 'bytes' in output or 'copied' in output:
                        # Try to extract bytes written
                        try:
                            # dd progress format varies, look for numbers
                            import re
                            numbers = re.findall(r'\d+', output)
                            if numbers:
                                bytes_written = int(numbers[0])
                                progress_percent = (bytes_written / file_size) * 100
                                progress_callback({
                                    'bytes_written': bytes_written,
                                    'total_bytes': file_size,
                                    'percent': min(progress_percent, 100),
                                    'status': output.strip()
                                })
                        except (ValueError, IndexError):
                            # Just pass the raw output if parsing fails
                            progress_callback({'status': output.strip()})
            
            # Wait for completion
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Successfully wrote archive to tape {device}")
                return True, bytes_written
            else:
                error_msg = f"dd command failed: {stderr}"
                logger.error(error_msg)
                return False, 0
                
        except Exception as e:
            logger.error(f"Error writing to tape: {e}")
            return False, 0
    
    def stream_to_tape(self, folder_path, device=None, compression=False, progress_callback=None):
        """Stream folder contents directly to tape using tar | dd."""
        if device is None:
            device = self.default_device
        
        if not self.dep_manager.tar_path or not self.dep_manager.dd_path:
            raise RuntimeError("tar and dd executables required for streaming")
        
        logger.info(f"Streaming {folder_path} directly to tape {device}")
        
        # Build tar command
        tar_cmd = [self.dep_manager.tar_path]
        
        if compression:
            tar_cmd.extend(['-czf', '-'])  # Compress and output to stdout
        else:
            tar_cmd.extend(['-cf', '-'])   # Output to stdout
        
        tar_cmd.extend(['-v', folder_path])  # Verbose and source folder
        
        # Build dd command
        dd_cmd = [
            self.dep_manager.dd_path,
            f'of={device}',
            f'bs={self.block_size}',
            'status=progress'
        ]
        
        try:
            # Start tar process
            tar_process = subprocess.Popen(
                tar_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False  # Binary output for tar
            )
            
            # Start dd process, taking input from tar
            dd_process = subprocess.Popen(
                dd_cmd,
                stdin=tar_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Close tar stdout in parent so dd can read from it
            tar_process.stdout.close()
            
            # Monitor progress from dd
            while True:
                output = dd_process.stderr.readline()
                
                if output == '' and dd_process.poll() is not None:
                    break
                
                if output and progress_callback:
                    progress_callback({'status': output.strip()})
            
            # Wait for both processes to complete
            tar_stdout, tar_stderr = tar_process.communicate()
            dd_stdout, dd_stderr = dd_process.communicate()
            
            # Check results
            if tar_process.returncode != 0:
                error_msg = f"tar command failed: {tar_stderr.decode()}"  
                logger.error(error_msg)
                return False
            
            if dd_process.returncode != 0:
                error_msg = f"dd command failed: {dd_stderr}"
                logger.error(error_msg)
                return False
            
            logger.info(f"Successfully streamed folder to tape {device}")
            return True
            
        except Exception as e:
            logger.error(f"Error streaming to tape: {e}")
            return False
    
    def verify_write(self, archive_path, device=None, original_checksum=None):
        """Verify tape write by reading back data (if possible)."""
        # Note: Verification by reading back from tape is complex
        # and may not be reliable with LTO drives.
        # This is a placeholder for future implementation.
        logger.warning("Tape verification not yet implemented")
        return True
    
    def eject_tape(self, device=None):
        """Eject the tape from the drive."""
        if device is None:
            device = self.default_device
        
        if not self.dep_manager.mt_path:
            logger.warning("mt command not available - cannot eject tape")
            return False
        
        try:
            logger.info(f"Ejecting tape from {device}...")
            result = subprocess.run(
                [self.dep_manager.mt_path, '-f', device, 'eject'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("Tape ejected successfully")
                return True
            else:
                logger.error(f"Failed to eject tape: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error ejecting tape: {e}")
            return False

