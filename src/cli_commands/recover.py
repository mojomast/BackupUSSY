#!/usr/bin/env python3
"""
Recover Command

Handles recovery operations for archives and files.
"""

import fnmatch

from .base import BaseCommand
from exceptions import ValidationError, RecoveryError


class RecoverCommand(BaseCommand):
    """Handle recover command and subcommands."""

    def execute(self, args) -> int:
        """Execute recover command."""
        action = getattr(args, 'recover_action', None)

        if not action:
            raise ValidationError("No recover action specified. Use 'recover --help' for options.")

        action_map = {
            'list': self._list_archives,
            'files': self._list_files,
            'start': self._recover_archive
        }

        if action in action_map:
            return action_map[action](args)
        else:
            raise ValidationError(f"Unknown recover action: {action}")

    def _list_archives(self, args) -> int:
        """List archives available for recovery."""
        tape_label = getattr(args, 'tape', None)
        limit = getattr(args, 'limit', 50)
        tape_id = None

        if tape_label:
            self.progress.status(f"Finding tape '{tape_label}'...")
            tape = self.db_manager.find_tape_by_label(tape_label)
            if not tape:
                raise ValidationError(f"Tape with label '{tape_label}' not found.")
            tape_id = tape['tape_id']
            self.progress.success(f"Found tape ID: {tape_id}")

        self.progress.status(f"Fetching recent archives (limit {limit})...")
        archives = self.db_manager.get_all_archives(tape_id=tape_id, limit=limit)

        if not archives:
            self.progress.info("No archives found matching the criteria.")
            return 0

        self.progress.success(f"Found {len(archives)} archives.")

        # Display results in a table
        headers = ["ID", "Archive Name", "Date", "Size", "Files", "Tape"]
        rows = []
        for archive in archives:
            rows.append([
                str(archive['archive_id']),
                archive['archive_name'],
                archive['archive_date'].split(' ')[0],  # Just the date part
                self.format_size(archive['archive_size_bytes']),
                f"{archive['file_count']:,}",
                archive['tape_label']
            ])
        
        self.print_table(headers, rows)
        return 0

    def _list_files(self, args) -> int:
        """List files within a specific archive."""
        archive_id = getattr(args, 'archive_id')
        filter_pattern = getattr(args, 'filter', None)

        self.progress.status(f"Fetching file list for archive ID: {archive_id}...")
        
        archive_details = self.db_manager.get_archive_details(archive_id)
        if not archive_details:
            raise RecoveryError(f"Archive with ID '{archive_id}' not found.")

        files = archive_details['files']

        if not files:
            self.progress.info(f"Archive '{archive_details['archive_name']}' contains no indexed files.")
            return 0

        if filter_pattern:
            self.progress.status(f"Filtering files with pattern: {filter_pattern}")
            files = [f for f in files if fnmatch.fnmatch(f['file_path'], filter_pattern)]

        if not files:
            self.progress.info(f"No files found matching filter '{filter_pattern}'.")
            return 0
            
        self.progress.success(f"Found {len(files)} files in archive '{archive_details['archive_name']}'.")

        headers = ["File Path", "Size", "Modified"]
        rows = []
        for f in files:
            rows.append([
                f['file_path'],
                self.format_size(f['file_size_bytes']),
                f['file_modified'].split('.')[0] # Remove microseconds
            ])
            
        self.print_table(headers, rows)
        return 0

    def _recover_archive(self, args) -> int:
        """Recover a full archive or specific files."""
        archive_id = getattr(args, 'archive_id')
        destination = getattr(args, 'destination')
        files_to_recover = getattr(args, 'files', [])
        overwrite = getattr(args, 'overwrite', False)
        preserve_structure = getattr(args, 'preserve_structure', True)
        device = getattr(args, 'device', None)

        # Validate destination path
        self._validate_path(destination, must_exist=True, is_dir=True)

        # Validate device if provided
        if device:
            self._validate_device(device)

        self.progress.status(f"Starting recovery for archive ID: {archive_id}")
        archive_details = self.db_manager.get_archive_details(archive_id)
        if not archive_details:
            raise RecoveryError(f"Archive with ID '{archive_id}' not found.")

        archive_name = archive_details['archive_name']
        tape_label = archive_details['tape']['tape_label']
        tape_device = device or archive_details['tape']['tape_device']

        if not tape_device:
            raise RecoveryError(
                f"No device specified and no default device found for tape '{tape_label}'. "
                f"Please specify with --device."
            )

        self.progress.info(f"Archive: {archive_name}")
        self.progress.info(f"Tape: {tape_label} ({tape_device})")
        self.progress.info(f"Destination: {destination}")

        # Validate files to recover if specified
        if files_to_recover:
            all_files_in_archive = {f['file_path'] for f in archive_details['files']}
            invalid_files = [f for f in files_to_recover if f not in all_files_in_archive]
            if invalid_files:
                raise ValidationError(f"The following files were not found in the archive: {', '.join(invalid_files)}")
            self.progress.info(f"Recovering {len(files_to_recover)} specific files.")
        else:
            self.progress.info("Recovering full archive.")

        def progress_callback(update):
            self.progress.status(update.get('status', '...'))
            if 'progress' in update:
                self.progress.update(update['progress'])

        try:
            if files_to_recover:
                success = self.recovery_manager.extract_specific_files(
                    tape_device=tape_device,
                    archive_name=archive_name,
                    file_list=files_to_recover,
                    output_dir=destination,
                    preserve_structure=preserve_structure,
                    overwrite=overwrite,
                    progress_callback=progress_callback
                )
            else:
                success = self.recovery_manager.extract_archive(
                    tape_device=tape_device,
                    archive_name=archive_name,
                    output_dir=destination,
                    overwrite=overwrite,
                    progress_callback=progress_callback
                )

            if success:
                self.progress.success("Recovery completed successfully.")
                return 0
            else:
                raise RecoveryError("Recovery failed. Check logs for details.")

        except Exception as e:
            raise RecoveryError(f"An unexpected error occurred during recovery: {e}")
