#!/usr/bin/env python3
"""
Archive Manager - Handles the core archiving logic and folder validation.
"""

import os
import subprocess
import hashlib
import tempfile
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from enum import Enum
from database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class ArchiveMode(Enum):
    """Archive modes supported by the tool."""
    STREAM = "stream"  # Stream directly to tape
    CACHED = "cached"  # Create archive file first, then write to tape

class ArchiveManager:
    """Manages the archiving process including folder validation and tar creation."""
    
    def __init__(self, dependency_manager, database_manager=None):
        self.dep_manager = dependency_manager
        self.db_manager = database_manager or DatabaseManager()
        self.temp_dir = None
        self.archive_path = None
        self.archive_checksum = None
        self.current_tape_id = None
        self.current_archive_id = None
    
    def validate_source_folder(self, folder_path):
        """Validate that the source folder exists and is readable."""
        if not folder_path:
            return False, "No folder specified"
        
        path = Path(folder_path)
        
        if not path.exists():
            return False, f"Folder does not exist: {folder_path}"
        
        if not path.is_dir():
            return False, f"Path is not a directory: {folder_path}"
        
        if not os.access(folder_path, os.R_OK):
            return False, f"Folder is not readable: {folder_path}"
        
        # Check if folder is empty
        try:
            if not any(path.iterdir()):
                return False, f"Folder is empty: {folder_path}"
        except PermissionError:
            return False, f"Permission denied accessing folder: {folder_path}"
        
        logger.info(f"Source folder validated: {folder_path}")
        return True, "Folder is valid"
    
    def estimate_archive_size(self, folder_path):
        """Estimate the size of the folder to be archived."""
        total_size = 0
        file_count = 0
        
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except (OSError, FileNotFoundError):
                        # Skip files that can't be accessed
                        continue
        except Exception as e:
            logger.warning(f"Error estimating folder size: {e}")
            return 0, 0
        
        logger.info(f"Estimated size: {total_size} bytes, {file_count} files")
        return total_size, file_count
    
    def generate_archive_name(self, folder_path, compression=False):
        """Generate a timestamped archive name."""
        folder_name = os.path.basename(os.path.abspath(folder_path))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if compression:
            extension = ".tar.gz"
        else:
            extension = ".tar"
        
        return f"{folder_name}_{timestamp}{extension}"
    
    def create_cached_archive(self, folder_path, output_dir=None, compression=False, 
                             progress_callback=None, tape_label=None, tape_device=None, 
                             index_files=True, archive_name_override=None):
        """Create a cached tar archive file, record it in DB, and return its info."""
        if not self.dep_manager.tar_path:
            raise RuntimeError("tar executable not available")
        
        # Set up output directory
        if output_dir is None:
            self.temp_dir = tempfile.mkdtemp(prefix="lto_archive_")
            output_dir = self.temp_dir
        
        # Determine archive name
        if archive_name_override:
            archive_name = archive_name_override
            if compression and not archive_name.endswith(('.tar.gz', '.tgz')):
                archive_name += '.tar.gz'
            elif not compression and not archive_name.endswith('.tar'):
                archive_name += '.tar'
        else:
            archive_name = self.generate_archive_name(folder_path, compression)
        self.archive_path = os.path.join(output_dir, archive_name)
        
        logger.info(f"Creating cached archive: {self.archive_path}")
        
        # Build tar command
        cmd = [self.dep_manager.tar_path]
        
        if compression:
            cmd.extend(['-czf', self.archive_path])
        else:
            cmd.extend(['-cf', self.archive_path])
        
        # Add verbose flag for progress
        cmd.append('-v')
        
        # Add the folder to archive
        cmd.append(folder_path)
        
        try:
            # Execute tar command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            
            # Monitor progress if callback provided
            if progress_callback:
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        progress_callback(output.strip())
            
            # Wait for completion
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                error_msg = f"tar command failed: {stderr}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            logger.info(f"Archive created successfully: {self.archive_path}")
            
            # Calculate checksum
            self.archive_checksum = self._calculate_checksum(self.archive_path)
            logger.info(f"Archive checksum (SHA256): {self.archive_checksum}")
            
            # Record in database if db_manager is available
            self.current_tape_id = None
            self.current_archive_id = None
            if self.db_manager:
                try:
                    if not tape_label or not tape_device:
                        logger.warning("Tape label or device not provided for DB record, attempting to use defaults or skip.")
                        # Fallback or error, depending on desired strictness. For now, we'll try to proceed if possible.
                        # If tape_label is crucial, this should raise an error or handle it more gracefully.
                        effective_tape_label = tape_label or f"Tape_{tape_device.replace('.', '').replace('\\', '') if tape_device else 'UnknownDevice'}"
                        effective_tape_device = tape_device or "UnknownDevice"
                    else:
                        effective_tape_label = tape_label
                        effective_tape_device = tape_device

                    # Add/get tape record
                    self.current_tape_id = self.db_manager.add_tape_if_not_exists(
                        effective_tape_label, 
                        effective_tape_device, 
                        tape_status='active',
                        notes=f"Tape used for cached archive of {folder_path}"
                    )

                    if self.current_tape_id is not None:
                        archive_size_bytes = os.path.getsize(self.archive_path)
                        num_files = self._count_files_in_folder(folder_path)

                        # Add archive record
                        self.current_archive_id = self.db_manager.add_archive(
                            tape_id=self.current_tape_id,
                            archive_name=archive_name, # Use the determined archive_name
                            source_folder=folder_path,
                            size_bytes=archive_size_bytes,
                            num_files=num_files,
                            archive_checksum=self.archive_checksum,
                            compression_enabled=compression,
                            status="completed" # Assuming cached archive is complete once created
                        )
                        logger.info(f"Archive record added to DB: ID={self.current_archive_id}, TapeID={self.current_tape_id}")

                        if index_files and self.current_archive_id:
                            logger.info(f"Indexing files for archive ID {self.current_archive_id}...")
                            self._index_archive_contents(folder_path, self.current_archive_id, progress_callback)
                            logger.info("File indexing completed for cached archive.")
                        elif not index_files:
                            logger.info("File indexing skipped by user setting for cached archive.")
                    else:
                        logger.error(f"Failed to get or create tape ID for {effective_tape_label}. Archive DB record skipped.")

                except Exception as e:
                    logger.error(f"Error during database operations for cached archive: {e}", exc_info=True)
                    # Depending on policy, we might want to set current_archive_id to None or re-raise
        
            return {
                'archive_path': self.archive_path,
                'archive_checksum': self.archive_checksum,
                'archive_id': self.current_archive_id
            }
            
        except Exception as e:
            logger.error(f"Error creating archive: {e}")
            # Clean up on failure
            if self.archive_path and os.path.exists(self.archive_path):
                os.remove(self.archive_path)
            raise
    
    def _calculate_checksum(self, file_path):
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def get_archive_info(self):
        """Get information about the current archive."""
        if not self.archive_path:
            return None
        
        try:
            stat = os.stat(self.archive_path)
            return {
                'path': self.archive_path,
                'size': stat.st_size,
                'checksum': self.archive_checksum,
                'created': datetime.fromtimestamp(stat.st_ctime)
            }
        except OSError:
            return None
    
    def cleanup(self):
        """Clean up temporary files and directories."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
            self.temp_dir = None
        
        self.archive_path = None
        self.archive_checksum = None
    
    def _count_files_in_folder(self, folder_path):
        """Count total number of files in folder recursively."""
        file_count = 0
        try:
            for root, dirs, files in os.walk(folder_path):
                file_count += len(files)
        except Exception as e:
            logger.warning(f"Error counting files: {e}")
        return file_count
    
    def _index_archive_contents(self, folder_path, archive_id, progress_callback=None):
        """Index all files in the folder into the database."""
        if not archive_id:
            return
        
        try:
            file_list = []
            total_files = 0
            processed_files = 0
            
            # First pass: count files for progress
            for root, dirs, files in os.walk(folder_path):
                total_files += len(files)
            
            # Second pass: collect file information
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        # Get relative path from archive root
                        rel_path = os.path.relpath(file_path, folder_path)
                        
                        # Get file stats
                        stat = os.stat(file_path)
                        file_size = stat.st_size
                        file_modified = datetime.fromtimestamp(stat.st_mtime)
                        
                        # Get file extension
                        file_type = os.path.splitext(file)[1].lower()
                        
                        file_info = {
                            'file_path': rel_path,
                            'file_size_bytes': file_size,
                            'file_modified': file_modified,
                            'file_type': file_type,
                            'file_checksum': None  # Optional: could implement file-level checksums
                        }
                        
                        file_list.append(file_info)
                        processed_files += 1
                        
                        # Update progress
                        if progress_callback and total_files > 0:
                            progress_percent = (processed_files / total_files) * 100
                            progress_callback(f"Indexing files: {processed_files}/{total_files} ({progress_percent:.1f}%)")
                        
                        # Batch insert files to avoid memory issues
                        if len(file_list) >= 1000:
                            self.db_manager.add_files(archive_id, file_list)
                            file_list = []
                        
                    except (OSError, PermissionError) as e:
                        logger.warning(f"Cannot access file {file_path}: {e}")
                        continue
            
            # Insert remaining files
            if file_list:
                self.db_manager.add_files(archive_id, file_list)
            
            logger.info(f"Indexed {processed_files} files for archive {archive_id}")
            
        except Exception as e:
            logger.error(f"Failed to index archive contents: {e}")
            raise
    
    def get_database_manager(self):
        """Get the database manager instance."""
        return self.db_manager
    
    def get_current_archive_info(self):
        """Get information about the current archive and tape."""
        return {
            'tape_id': self.current_tape_id,
            'archive_id': self.current_archive_id,
            'archive_path': self.archive_path,
            'archive_checksum': self.archive_checksum
        }
    
    def find_archives_by_folder(self, folder_path):
        """Find all archives that contain the specified folder."""
        if not self.db_manager:
            return []
        
        try:
            # Search for archives with matching source folder
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT a.*, t.tape_label, t.tape_device, t.tape_status
                    FROM archives a
                    JOIN tapes t ON a.tape_id = t.tape_id
                    WHERE a.source_folder LIKE ?
                    ORDER BY a.archive_date DESC
                """, (f"%{folder_path}%",))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to find archives by folder: {e}")
            return []
    
    def suggest_tape_for_new_archive(self, estimated_size_bytes):
        """Suggest the best tape for a new archive based on available space."""
        if not self.db_manager:
            return None
        
        try:
            # Get all active tapes with their usage
            tapes = self.db_manager.get_all_tapes()
            
            # Filter active tapes and calculate remaining space
            # (Assuming LTO-7 capacity of ~6TB = 6,000,000,000,000 bytes)
            MAX_TAPE_CAPACITY = 6_000_000_000_000  # 6TB
            
            suitable_tapes = []
            for tape in tapes:
                if tape['tape_status'] == 'active':
                    used_space = tape['total_size_bytes'] or 0
                    remaining_space = MAX_TAPE_CAPACITY - used_space
                    
                    if remaining_space >= estimated_size_bytes:
                        tape['remaining_space'] = remaining_space
                        suitable_tapes.append(tape)
            
            # Sort by least remaining space (most efficient packing)
            suitable_tapes.sort(key=lambda x: x['remaining_space'])
            
            if suitable_tapes:
                best_tape = suitable_tapes[0]
                logger.info(f"Suggested tape: {best_tape['tape_label']} (remaining: {best_tape['remaining_space']/1024/1024/1024:.1f} GB)")
                return best_tape
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to suggest tape: {e}")
            return None
    
    def __del__(self):
        """Ensure cleanup on object destruction."""
        self.cleanup()

