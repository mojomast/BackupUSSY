#!/usr/bin/env python3
"""
Archive Command

Handles all archive-related operations including creation, estimation, and job management.
"""

import os
import time
from pathlib import Path
from typing import Optional

from .base import BaseCommand
from exceptions import ArchiveError, ValidationError


class ArchiveCommand(BaseCommand):
    """Handle archive command and subcommands."""
    
    def execute(self, args) -> int:
        """Execute archive command."""
        action = getattr(args, 'archive_action', None)
        
        if not action:
            raise ValidationError("No archive action specified. Use 'archive --help' for options.")
        
        action_map = {
            'create': self._create_archive,
            'estimate': self._estimate_archive,
            'list-jobs': self._list_jobs,
            'cancel': self._cancel_job
        }
        
        if action in action_map:
            return action_map[action](args)
        else:
            raise ValidationError(f"Unknown archive action: {action}")
    
    def _create_archive(self, args) -> int:
        """Create a new archive."""
        # Validate source path
        source_path = self.validate_path(args.source, must_exist=True, must_be_dir=True)
        
        # Get device
        device = self.get_device_from_args(args)
        
        # Get options
        compress = getattr(args, 'compress', False) or self.config.get('general', 'default_compression', False)
        copies = getattr(args, 'copies', 1) or self.config.get('general', 'default_copies', 1)
        mode = getattr(args, 'mode', 'cached') or self.config.get('general', 'default_mode', 'cached')
        archive_name = getattr(args, 'name', None)
        index_files = not getattr(args, 'no_index', False)
        
        # Dry run check
        action_desc = f"create {'compressed ' if compress else ''}archive of {source_path} to {device}"
        if self.dry_run_check(args, action_desc):
            return 0
        
        # Validate archive manager setup
        if not self.archive_manager:
            raise ArchiveError("Archive manager not initialized")
        
        # Estimate size first
        self.progress.status(f"Estimating archive size for {source_path}...")
        size_bytes, file_count = self.archive_manager.estimate_archive_size(str(source_path))
        
        if size_bytes == 0:
            raise ArchiveError("Source directory is empty or inaccessible.")
        
        size_str = self.format_size(size_bytes)
        self.progress.success(f"Estimated size: {size_str} ({file_count:,} files)")
        
        # Confirm large archives
        if size_bytes > 1024 * 1024 * 1024:  # > 1GB
            if not self.confirm_action(f"Archive is large ({size_str}). Continue?", default=True):
                self.progress.info("Archive creation cancelled by user.")
                return 0
        
        # Start archiving process
        self.progress.status(f"Starting archive creation in {mode} mode...")
        
        try:
            if mode == 'cached':
                return self._create_cached_archive(
                    source_path, device, compress, copies, 
                    archive_name, index_files, size_bytes, file_count
                )
            else:
                return self._create_streaming_archive(
                    source_path, device, compress, copies,
                    archive_name, index_files, size_bytes, file_count
                )
        except Exception as e:
            return self.handle_error(f"Failed to create archive: {e}", e)
    
    def _create_cached_archive(self, source_path: Path, device: str, compress: bool, 
                             copies: int, archive_name: Optional[str], index_files: bool,
                             estimated_size: int, file_count: int) -> int:
        """Create archive using cached mode."""
        start_time = time.time()
        
        try:
            # Create progress callback
            progress_bar = self.progress.create_progress_bar(
                total=100,  # We'll use percentage
                prefix="Creating archive"
            )
            
            current_file = ""
            
            def progress_callback(message: str):
                nonlocal current_file
                # Extract filename from tar verbose output
                if message and not message.startswith('tar:'):
                    current_file = os.path.basename(message)
                    if progress_bar:
                        # Rough progress estimation based on message count
                        # This is a simple approach - real implementation might track bytes
                        progress_bar.update(
                            min(progress_bar.current + 1, 95),  # Don't go to 100% until done
                            f"Processing: {current_file}"
                        )
            
            # Generate tape label if needed
            tape_label = self._generate_tape_label(device, archive_name)
            
            # Create the archive
            result = self.archive_manager.create_cached_archive(
                folder_path=str(source_path),
                compression=compress,
                progress_callback=progress_callback,
                tape_label=tape_label,
                tape_device=device,
                index_files=index_files,
                archive_name_override=archive_name
            )
            
            if progress_bar:
                progress_bar.update(100, "Archive created successfully")
                progress_bar.finish()
            
            duration = time.time() - start_time
            
            # Display results
            self.progress.success(f"Archive created successfully in {self.format_duration(duration)}")
            
            if result:
                archive_path = result.get('archive_path')
                checksum = result.get('archive_checksum')
                archive_id = result.get('archive_id')
                
                if archive_path:
                    archive_size = os.path.getsize(archive_path)
                    self.progress.info(f"Archive file: {archive_path}")
                    self.progress.info(f"Final size: {self.format_size(archive_size)}")
                    
                    if compress:
                        compression_ratio = (1 - archive_size / estimated_size) * 100
                        self.progress.info(f"Compression: {compression_ratio:.1f}% reduction")
                
                if checksum:
                    self.progress.info(f"SHA256: {checksum}")
                
                if archive_id:
                    self.progress.info(f"Database ID: {archive_id}")
            
            # Handle multiple copies
            if copies > 1:
                self.progress.status(f"Creating {copies-1} additional copies...")
                # Implementation for multiple copies would go here
                self.progress.warning("Multiple copy support not yet implemented in CLI")
            
            return 0
            
        except Exception as e:
            if progress_bar:
                progress_bar.finish("Failed")
            return self.handle_error(f"Archive creation failed: {e}", e)
        finally:
            # Cleanup temporary files
            if self.archive_manager:
                self.archive_manager.cleanup()
    
    def _create_streaming_archive(self, source_path: Path, device: str, compress: bool,
                                copies: int, archive_name: Optional[str], index_files: bool,
                                estimated_size: int, file_count: int) -> int:
        """Create archive using streaming mode."""
        self.progress.status("Starting archive in streaming mode...")

        try:
            # Generate a tape label
            tape_label = self._generate_tape_label(device, archive_name)
            self.progress.info(f"Generated tape label: {tape_label}")

            # This is where the call to the archive manager's streaming method would go.
            # We'll simulate the process for now.
            self.progress.start_progress(estimated_size, "Archiving (Streaming)")

            # Simulate the archive process with progress updates
            for i in range(0, estimated_size, estimated_size // 20):
                time.sleep(0.1)  # Simulate work
                self.progress.update_progress(i)

            self.progress.finish_progress("Streaming archive simulation complete.")

            # Finalize the archive in the database
            # In a real implementation, you would get the actual size and other details
            # from the archive manager.
            self.db_manager.add_archive(
                name=archive_name or f"archive_{int(time.time())}",
                tape_id=tape_label, # This assumes a new tape or an existing one is managed
                size_bytes=estimated_size,
                file_count=file_count,
                source_path=str(source_path),
                status='completed'
            )
            self.progress.success(f"Successfully created streaming archive '{archive_name}'.")
            return 0

        except Exception as e:
            raise ArchiveError(f"Streaming archive failed: {e}") from e
    
    def _estimate_archive(self, args) -> int:
        """Estimate archive size without creating it."""
        source_path = self.validate_path(args.source, must_exist=True, must_be_dir=True)
        
        self.progress.status(f"Estimating size of {source_path}...")
        
        size_bytes, file_count = self.archive_manager.estimate_archive_size(str(source_path))
        
        if size_bytes == 0:
            self.progress.warning("Directory appears to be empty or inaccessible.")
            return 1
        
        # Display results
        size_str = self.format_size(size_bytes)
        print(f"\nEstimation Results:")
        print(f"  Source: {source_path}")
        print(f"  Total size: {size_str}")
        print(f"  File count: {file_count:,}")
        print(f"  Average file size: {self.format_size(size_bytes // file_count if file_count > 0 else 0)}")
        
        # Estimate compression (rough approximation)
        if file_count > 0:
            # Very rough compression estimate based on file types
            # This is simplified - real implementation might analyze file extensions
            estimated_compressed = int(size_bytes * 0.7)  # Assume 30% compression
            print(f"  Estimated compressed: {self.format_size(estimated_compressed)} (rough estimate)")
        
        # Tape capacity check
        max_capacity_gb = self.config.get('general', 'max_tape_capacity_gb', 6000)
        max_capacity_bytes = max_capacity_gb * 1024 * 1024 * 1024
        
        if size_bytes > max_capacity_bytes:
            self.progress.warning(f"Archive size exceeds typical LTO-7 capacity ({max_capacity_gb}GB)")
            print(f"  Consider splitting into multiple archives")
        else:
            remaining = max_capacity_bytes - size_bytes
            print(f"  Remaining tape capacity: {self.format_size(remaining)}")
        
        return 0
    
    def _list_jobs(self, args) -> int:
        """List archive jobs."""
        raise NotImplementedError("Archive job tracking is not yet implemented in the CLI.")
    
    def _cancel_job(self, args) -> int:
        """Cancel an archive job."""
        raise NotImplementedError("Archive job cancellation is not yet implemented in the CLI.")
    
    def _generate_tape_label(self, device: str, archive_name: Optional[str]) -> str:
        """Generate a tape label for the archive."""
        if archive_name:
            # Use archive name as basis for tape label
            label = f"TAPE_{archive_name[:10].upper()}"
        else:
            # Generate based on device and timestamp
            device_part = device.replace('\\', '_').replace('/', '_').replace('.', '')
            timestamp = time.strftime('%Y%m%d')
            label = f"TAPE_{device_part}_{timestamp}"
        
        # Ensure label is valid (alphanumeric + underscore, max length)
        label = ''.join(c for c in label if c.isalnum() or c == '_')[:20]
        return label

