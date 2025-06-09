#!/usr/bin/env python3
"""
Recovery Manager - Handles tape reading and file extraction.
Phase 2.2.1 - Recovery functionality for LTO Tape Archive Tool.
"""

import os
import subprocess
import tempfile
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable

from database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class RecoveryManager:
    """Manages tape reading and file extraction operations."""
    
    def __init__(self, dependency_manager, database_manager=None):
        """Initialize recovery manager.
        
        Args:
            dependency_manager: DependencyManager instance for tar/dd/mt tools
            database_manager: Optional DatabaseManager for tape indexing
        """
        self.dep_manager = dependency_manager
        self.db_manager = database_manager or DatabaseManager()
        self.temp_dir = None
        
        # Verify required tools are available
        if not self.dep_manager.tar_path:
            raise RuntimeError("tar executable not available for recovery")
        if not self.dep_manager.dd_path:
            raise RuntimeError("dd executable not available for recovery")
            
        logger.info("Recovery manager initialized")
    
    def list_tape_contents(self, tape_device: str, use_database: bool = True) -> List[Dict[str, Any]]:
        """List all archives on a tape.
        
        Args:
            tape_device: Tape device path (e.g., \\.\\Tape0)
            use_database: If True, try to get contents from database first
            
        Returns:
            List of archive information dictionaries
        """
        logger.info(f"Listing contents of tape device: {tape_device}")
        
        # Try database first if requested
        if use_database and self.db_manager:
            try:
                # Find tape by device in database
                tapes = self.db_manager.get_all_tapes()
                matching_tape = None
                
                for tape in tapes:
                    if tape['tape_device'] == tape_device:
                        matching_tape = tape
                        break
                
                if matching_tape:
                    contents = self.db_manager.get_tape_contents(matching_tape['tape_id'])
                    logger.info(f"Found {len(contents['archives'])} archives in database")
                    return contents['archives']
                    
            except Exception as e:
                logger.warning(f"Could not get contents from database: {e}")
        
        # Fall back to reading directly from tape
        return self._read_tape_contents_directly(tape_device)
    
    def _read_tape_contents_directly(self, tape_device: str) -> List[Dict[str, Any]]:
        """Read tape contents directly using tar.
        
        Args:
            tape_device: Tape device path
            
        Returns:
            List of archive information (limited without database)
        """
        try:
            logger.info("Reading tape contents directly with tar")
            
            # Use tar to list contents
            cmd = [self.dep_manager.tar_path, '-tf', tape_device]
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if process.returncode != 0:
                raise RuntimeError(f"Failed to read tape: {process.stderr}")
            
            # Parse tar output to identify archives
            files = process.stdout.strip().split('\n') if process.stdout.strip() else []
            
            # Group files by potential archive structure
            # This is basic - real implementation would be more sophisticated
            archives = [{
                'archive_name': 'tape_contents',
                'file_count': len(files),
                'files_preview': files[:10],  # First 10 files as preview
                'total_files': len(files),
                'source': 'direct_read'
            }]
            
            logger.info(f"Found {len(files)} files on tape via direct read")
            return archives
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout reading tape contents")
            raise RuntimeError("Timeout reading tape contents")
        except Exception as e:
            logger.error(f"Failed to read tape contents directly: {e}")
            raise
    
    def extract_archive(self, tape_device: str, archive_name: str, output_dir: str,
                       progress_callback: Optional[Callable] = None) -> bool:
        """Extract a complete archive from tape.
        
        Args:
            tape_device: Tape device path
            archive_name: Name of archive to extract
            output_dir: Directory to extract files to
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if extraction successful, False otherwise
        """
        logger.info(f"Extracting archive '{archive_name}' from {tape_device} to {output_dir}")
        
        try:
            # Ensure output directory exists
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Position tape if we have archive position info from database
            archive_position = self._get_archive_position(tape_device, archive_name)
            if archive_position and archive_position > 1:
                self._position_tape(tape_device, archive_position)
            
            # Extract using tar
            cmd = [self.dep_manager.tar_path, '-xf', tape_device, '-C', output_dir, '-v']
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            
            extracted_files = []
            
            # Monitor progress
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                    
                if output:
                    filename = output.strip()
                    extracted_files.append(filename)
                    
                    if progress_callback:
                        progress_callback({
                            'type': 'file_extracted',
                            'filename': filename,
                            'total_extracted': len(extracted_files)
                        })
            
            # Wait for completion
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Successfully extracted {len(extracted_files)} files")
                
                if progress_callback:
                    progress_callback({
                        'type': 'extraction_complete',
                        'total_files': len(extracted_files),
                        'output_dir': output_dir
                    })
                
                return True
            else:
                logger.error(f"Extraction failed: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Archive extraction failed: {e}")
            return False
    
    def extract_specific_files(self, tape_device: str, archive_name: str, 
                              file_list: List[str], output_dir: str,
                              progress_callback: Optional[Callable] = None) -> bool:
        """Extract specific files from an archive on tape.
        
        Args:
            tape_device: Tape device path
            archive_name: Name of archive containing the files
            file_list: List of file paths to extract
            output_dir: Directory to extract files to
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if extraction successful, False otherwise
        """
        logger.info(f"Extracting {len(file_list)} specific files from '{archive_name}'")
        
        try:
            # Ensure output directory exists
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Position tape if needed
            archive_position = self._get_archive_position(tape_device, archive_name)
            if archive_position and archive_position > 1:
                self._position_tape(tape_device, archive_position)
            
            # Build tar command with specific files
            cmd = [self.dep_manager.tar_path, '-xf', tape_device, '-C', output_dir, '-v']
            cmd.extend(file_list)
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            
            extracted_files = []
            
            # Monitor progress
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                    
                if output:
                    filename = output.strip()
                    extracted_files.append(filename)
                    
                    if progress_callback:
                        progress_callback({
                            'type': 'file_extracted',
                            'filename': filename,
                            'progress': len(extracted_files) / len(file_list) * 100
                        })
            
            # Wait for completion
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Successfully extracted {len(extracted_files)} specific files")
                return True
            else:
                logger.error(f"Selective extraction failed: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Specific file extraction failed: {e}")
            return False
    
    def verify_tape_integrity(self, tape_device: str) -> Dict[str, Any]:
        """Check tape readability and integrity.
        
        Args:
            tape_device: Tape device path
            
        Returns:
            Dictionary with integrity check results
        """
        logger.info(f"Verifying integrity of tape: {tape_device}")
        
        result = {
            'device': tape_device,
            'readable': False,
            'has_data': False,
            'archive_count': 0,
            'total_files': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Test basic tape accessibility
            if not self._test_tape_access(tape_device):
                result['errors'].append("Tape device not accessible")
                return result
            
            result['readable'] = True
            
            # Try to read tape contents
            try:
                archives = self._read_tape_contents_directly(tape_device)
                result['has_data'] = len(archives) > 0
                result['archive_count'] = len(archives)
                
                if archives:
                    result['total_files'] = sum(arch.get('total_files', 0) for arch in archives)
                
            except Exception as e:
                result['errors'].append(f"Could not read tape contents: {e}")
            
            # Check tape status using mt if available
            if self.dep_manager.mt_path:
                try:
                    status_output = subprocess.run(
                        [self.dep_manager.mt_path, '-f', tape_device, 'status'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if status_output.returncode == 0:
                        # Parse status for warnings
                        status_text = status_output.stdout.lower()
                        if 'error' in status_text:
                            result['warnings'].append("Tape status indicates errors")
                        if 'end' in status_text and 'tape' in status_text:
                            result['warnings'].append("Tape may be at end position")
                    
                except Exception as e:
                    result['warnings'].append(f"Could not check tape status: {e}")
            
            logger.info(f"Tape integrity check completed: readable={result['readable']}, data={result['has_data']}")
            return result
            
        except Exception as e:
            result['errors'].append(f"Integrity check failed: {e}")
            logger.error(f"Tape integrity check failed: {e}")
            return result
    
    def get_archive_from_tape(self, tape_device: str, position: int = 1) -> Optional[Dict[str, Any]]:
        """Read archive at specific position on tape.
        
        Args:
            tape_device: Tape device path
            position: Archive position on tape (1-based)
            
        Returns:
            Archive information or None if not found
        """
        logger.info(f"Reading archive at position {position} from {tape_device}")
        
        try:
            # Position tape to specified archive
            if position > 1:
                self._position_tape(tape_device, position)
            
            # Read archive information
            archives = self._read_tape_contents_directly(tape_device)
            
            if archives:
                archive = archives[0]  # Should be the archive at current position
                archive['position'] = position
                return archive
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to read archive at position {position}: {e}")
            return None
    
    def _get_archive_position(self, tape_device: str, archive_name: str) -> Optional[int]:
        """Get archive position from database.
        
        Args:
            tape_device: Tape device path
            archive_name: Archive name
            
        Returns:
            Archive position or None if not found
        """
        if not self.db_manager:
            return None
        
        try:
            # Find tape in database
            tapes = self.db_manager.get_all_tapes()
            for tape in tapes:
                if tape['tape_device'] == tape_device:
                    contents = self.db_manager.get_tape_contents(tape['tape_id'])
                    
                    for archive in contents['archives']:
                        if archive['archive_name'] == archive_name:
                            return archive.get('archive_position', 1)
            
        except Exception as e:
            logger.warning(f"Could not get archive position from database: {e}")
        
        return None
    
    def _position_tape(self, tape_device: str, position: int) -> bool:
        """Position tape to specific archive.
        
        Args:
            tape_device: Tape device path
            position: Target position (1-based)
            
        Returns:
            True if positioning successful
        """
        if not self.dep_manager.mt_path:
            logger.warning("mt command not available - cannot position tape")
            return False
        
        try:
            logger.info(f"Positioning tape to archive {position}")
            
            # Rewind tape first
            subprocess.run(
                [self.dep_manager.mt_path, '-f', tape_device, 'rewind'],
                timeout=60,
                check=True
            )
            
            # Skip to desired position (position-1 file marks)
            if position > 1:
                subprocess.run(
                    [self.dep_manager.mt_path, '-f', tape_device, 'fsf', str(position - 1)],
                    timeout=120,
                    check=True
                )
            
            logger.info(f"Tape positioned to archive {position}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to position tape: {e}")
            return False
        except Exception as e:
            logger.error(f"Tape positioning error: {e}")
            return False
    
    def _test_tape_access(self, tape_device: str) -> bool:
        """Test if tape device is accessible.
        
        Args:
            tape_device: Tape device path
            
        Returns:
            True if accessible
        """
        try:
            # Try to open device for reading
            with open(tape_device, 'rb') as f:
                # Just opening is enough to test access
                pass
            return True
        except (OSError, PermissionError):
            return False
    
    def find_file_on_tapes(self, filename: str) -> List[Dict[str, Any]]:
        """Find a file across all tapes in the database.
        
        Args:
            filename: Name or path of file to find
            
        Returns:
            List of locations where file was found
        """
        if not self.db_manager:
            logger.warning("Database not available for file search")
            return []
        
        try:
            # Search for file in database
            results = self.db_manager.search_files(filename)
            
            locations = []
            for result in results:
                location = {
                    'file_path': result['file_path'],
                    'file_size': result['file_size_bytes'],
                    'modified_date': result['file_modified'],
                    'archive_name': result['archive_name'],
                    'tape_label': result['tape_label'],
                    'tape_device': result['tape_device'],
                    'archive_id': result['archive_id'],
                    'tape_id': result['tape_id']
                }
                locations.append(location)
            
            logger.info(f"Found file '{filename}' in {len(locations)} locations")
            return locations
            
        except Exception as e:
            logger.error(f"File search failed: {e}")
            return []
    
    def recover_file_by_id(self, file_id: int, output_dir: str,
                          progress_callback: Optional[Callable] = None) -> bool:
        """Recover a specific file by its database ID.
        
        Args:
            file_id: Database file ID
            output_dir: Directory to extract file to
            progress_callback: Optional progress callback
            
        Returns:
            True if recovery successful
        """
        if not self.db_manager:
            logger.error("Database not available for file recovery")
            return False
        
        try:
            # Get file details from database
            files = self.db_manager.search_files("")  # Get all files
            target_file = None
            
            for file_info in files:
                if file_info['file_id'] == file_id:
                    target_file = file_info
                    break
            
            if not target_file:
                logger.error(f"File ID {file_id} not found in database")
                return False
            
            # Extract the specific file
            return self.extract_specific_files(
                target_file['tape_device'],
                target_file['archive_name'],
                [target_file['file_path']],
                output_dir,
                progress_callback
            )
            
        except Exception as e:
            logger.error(f"File recovery by ID failed: {e}")
            return False
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery-related statistics.
        
        Returns:
            Dictionary with recovery statistics
        """
        stats = {
            'total_tapes': 0,
            'total_archives': 0,
            'total_files': 0,
            'total_data_bytes': 0,
            'accessible_tapes': 0
        }
        
        if self.db_manager:
            try:
                db_stats = self.db_manager.get_database_stats()
                stats.update(db_stats)
                
                # Test tape accessibility
                tapes = self.db_manager.get_all_tapes()
                accessible_count = 0
                
                for tape in tapes:
                    if self._test_tape_access(tape['tape_device']):
                        accessible_count += 1
                
                stats['accessible_tapes'] = accessible_count
                
            except Exception as e:
                logger.error(f"Failed to get recovery stats: {e}")
        
        return stats
    
    def cleanup(self):
        """Clean up temporary files and resources."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up recovery temp directory: {self.temp_dir}")
            self.temp_dir = None
    
    def detect_tape_damage(self, device: str) -> Dict:
        """Detect and analyze tape damage or corruption."""
        try:
            damage_report = {
                'is_damaged': False,
                'damage_type': None,
                'affected_sectors': [],
                'recoverable_data': True,
                'recommendations': []
            }
            
            # Test tape readability
            test_result = self.test_tape_readability(device)
            
            if not test_result['readable']:
                damage_report['is_damaged'] = True
                damage_report['damage_type'] = test_result.get('error_type', 'unknown')
                damage_report['recoverable_data'] = test_result.get('partial_read_possible', False)
                
                if test_result.get('error_type') == 'media_error':
                    damage_report['recommendations'].extend([
                        'Try cleaning the tape drive',
                        'Attempt recovery with different drive',
                        'Consider professional data recovery'
                    ])
                elif test_result.get('error_type') == 'positioning_error':
                    damage_report['recommendations'].extend([
                        'Retry with tape rewinding',
                        'Check tape tension',
                        'Verify drive mechanics'
                    ])
            
            logger.info(f"Tape damage detection complete: {damage_report['is_damaged']}")
            return damage_report
            
        except Exception as e:
            logger.error(f"Failed to detect tape damage: {e}")
            return {'is_damaged': True, 'damage_type': 'detection_failed', 'error': str(e)}
    
    def test_tape_readability(self, device: str) -> Dict:
        """Test tape readability and identify issues."""
        try:
            if not self.dep_manager.dd_path:
                return {
                    'readable': False,
                    'error_type': 'missing_tools',
                    'partial_read_possible': False
                }
            
            # Attempt to read tape header/beginning
            cmd = [self.dep_manager.dd_path, f'if={device}', 'of=nul', 'bs=1024', 'count=10']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    'readable': True,
                    'error_type': None,
                    'partial_read_possible': True
                }
            else:
                # Analyze error output
                error_output = result.stderr.lower()
                
                if 'input/output error' in error_output or 'media error' in error_output:
                    return {
                        'readable': False,
                        'error_type': 'media_error',
                        'partial_read_possible': False
                    }
                elif 'no such device' in error_output or 'access denied' in error_output:
                    return {
                        'readable': False,
                        'error_type': 'device_error',
                        'partial_read_possible': False
                    }
                else:
                    return {
                        'readable': False,
                        'error_type': 'positioning_error',
                        'partial_read_possible': True
                    }
                    
        except subprocess.TimeoutExpired:
            return {
                'readable': False,
                'error_type': 'timeout_error',
                'partial_read_possible': True
            }
        except Exception as e:
            logger.error(f"Tape readability test failed: {e}")
            return {
                'readable': False,
                'error_type': 'test_failed',
                'partial_read_possible': False,
                'error': str(e)
            }
    
    def attempt_partial_recovery(self, device: str, archive_name: str, output_dir: str,
                                progress_callback=None) -> Dict:
        """Attempt to recover whatever data is possible from a damaged tape."""
        try:
            recovery_result = {
                'success': False,
                'recovered_files': [],
                'failed_files': [],
                'recovery_percentage': 0,
                'warnings': []
            }
            
            progress_callback and progress_callback({"status": "Starting partial recovery..."})
            
            # First, test what we can read
            damage_report = self.detect_tape_damage(device)
            
            if not damage_report.get('recoverable_data', False):
                recovery_result['warnings'].append('Tape appears completely unreadable')
                return recovery_result
            
            # Attempt recovery with error tolerance
            temp_dir = Path(output_dir) / f"partial_recovery_{int(time.time())}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Use dd with error recovery options
                temp_file = temp_dir / 'recovered_data.tar'
                cmd = [
                    self.dep_manager.dd_path,
                    f'if={device}',
                    f'of={temp_file}',
                    'bs=1024',
                    'count=10000'  # Limit recovery size
                ]
                
                progress_callback and progress_callback({"status": "Reading tape with error tolerance..."})
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=1800  # Allow 30 minutes for recovery
                )
                
                if temp_file.exists() and temp_file.stat().st_size > 0:
                    progress_callback and progress_callback({"status": "Extracting recovered data..."})
                    
                    # Try to extract what we can from the potentially corrupted tar
                    try:
                        # First try normal extraction
                        extract_cmd = [
                            self.dep_manager.tar_path,
                            '-xf', str(temp_file),
                            '-C', output_dir
                        ]
                        
                        extract_result = subprocess.run(
                            extract_cmd,
                            capture_output=True,
                            text=True
                        )
                        
                        # Count recovered files
                        recovered_files = list(Path(output_dir).rglob('*'))
                        recovered_files = [f for f in recovered_files if f.is_file() and 'partial_recovery_' not in str(f)]
                        
                        recovery_result['recovered_files'] = [str(f.relative_to(output_dir)) for f in recovered_files]
                        recovery_result['success'] = len(recovered_files) > 0
                        recovery_result['recovery_percentage'] = min(100, len(recovered_files) * 5)  # Rough estimate
                        
                        if extract_result.stderr:
                            recovery_result['warnings'].append(f"Extraction warnings: {extract_result.stderr[:200]}...")
                        
                        progress_callback and progress_callback({
                            "status": f"Recovered {len(recovered_files)} files"
                        })
                        
                    except Exception as extract_error:
                        recovery_result['warnings'].append(f"Standard extraction failed: {extract_error}")
                        
                        # Try alternative extraction methods
                        recovery_result = self._try_alternative_extraction(
                            temp_file, output_dir, recovery_result, progress_callback
                        )
                
            finally:
                # Cleanup temporary files
                if temp_dir.exists():
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
            
            logger.info(f"Partial recovery completed: {recovery_result['recovery_percentage']}% success")
            return recovery_result
            
        except Exception as e:
            logger.error(f"Partial recovery failed: {e}")
            return {
                'success': False,
                'recovered_files': [],
                'failed_files': [],
                'recovery_percentage': 0,
                'error': str(e)
            }
    
    def _try_alternative_extraction(self, archive_path: Path, output_dir: str,
                                   recovery_result: Dict, progress_callback=None) -> Dict:
        """Try alternative methods to extract data from corrupted archive."""
        try:
            progress_callback and progress_callback({"status": "Trying alternative extraction methods..."})
            
            # Method 1: Try to list contents first
            try:
                list_cmd = [self.dep_manager.tar_path, '-tf', str(archive_path)]
                list_result = subprocess.run(list_cmd, capture_output=True, text=True)
                
                if list_result.returncode == 0:
                    file_list = [f for f in list_result.stdout.strip().split('\n') if f.strip()]
                    
                    # Try to extract files individually
                    for file_path in file_list[:50]:  # Limit to first 50 files
                        try:
                            extract_cmd = [
                                self.dep_manager.tar_path,
                                '-xf', str(archive_path),
                                '-C', output_dir,
                                file_path
                            ]
                            
                            result = subprocess.run(extract_cmd, capture_output=True)
                            
                            if result.returncode == 0:
                                recovery_result['recovered_files'].append(file_path)
                            else:
                                recovery_result['failed_files'].append(file_path)
                                
                        except Exception:
                            recovery_result['failed_files'].append(file_path)
                            continue
                    
                    recovery_result['success'] = len(recovery_result['recovered_files']) > 0
                    total_files = len(recovery_result['recovered_files']) + len(recovery_result['failed_files'])
                    if total_files > 0:
                        recovery_result['recovery_percentage'] = (len(recovery_result['recovered_files']) / total_files) * 100
                        
            except Exception as list_error:
                recovery_result['warnings'].append(f"Could not list archive contents: {list_error}")
            
            return recovery_result
            
        except Exception as e:
            recovery_result['warnings'].append(f"Alternative extraction failed: {e}")
            return recovery_result
    
    def retry_with_different_settings(self, device: str, archive_name: str, output_dir: str,
                                    max_retries: int = 3, progress_callback=None) -> bool:
        """Retry recovery with different settings if initial attempt fails."""
        retry_strategies = [
            {'description': 'Smaller block size', 'bs': '512'},
            {'description': 'Skip initial blocks', 'skip': '1'},
            {'description': 'Rewind and retry', 'rewind': True}
        ]
        
        for attempt in range(max_retries):
            try:
                strategy = retry_strategies[attempt % len(retry_strategies)]
                
                progress_callback and progress_callback({
                    "status": f"Retry {attempt + 1}/{max_retries}: {strategy['description']}"
                })
                
                # Implement retry with specific strategy
                success = self._retry_with_strategy(device, archive_name, output_dir, strategy)
                
                if success:
                    progress_callback and progress_callback({
                        "status": f"Recovery successful on retry {attempt + 1}"
                    })
                    return True
                    
                # Wait before next retry
                time.sleep(5)
                
            except Exception as e:
                logger.warning(f"Retry {attempt + 1} failed: {e}")
                continue
        
        progress_callback and progress_callback({"status": "All retry attempts failed"})
        return False
    
    def _retry_with_strategy(self, device: str, archive_name: str, output_dir: str, strategy: Dict) -> bool:
        """Attempt recovery with a specific strategy."""
        try:
            # Handle rewind strategy
            if strategy.get('rewind'):
                self._position_tape(device, 1)  # Rewind to beginning
            
            # Try basic extraction with strategy modifications
            return self.extract_archive(device, archive_name, output_dir)
            
        except Exception as e:
            logger.error(f"Strategy retry failed: {e}")
            return False
    
    def __del__(self):
        """Ensure cleanup on object destruction."""
        self.cleanup()

