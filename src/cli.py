#!/usr/bin/env python3
"""
Backupussy CLI - Terminal-based interface for LTO tape backup system

This module provides a command-line interface that mirrors all functionality
of the GUI-based backup system, enabling automation and scripting.
"""

import sys
import argparse
import logging
import os
from pathlib import Path
from datetime import datetime

# Import existing backend managers
from main import DependencyManager
from archive_manager import ArchiveManager
from tape_manager import TapeManager
from database_manager import DatabaseManager
from recovery_manager import RecoveryManager
from search_interface import SearchInterface
from tape_library import TapeLibrary

# Import CLI command modules (to be created)
from cli_commands.archive import ArchiveCommand
from cli_commands.recover import RecoverCommand
from cli_commands.search import SearchCommand
from cli_commands.manage import ManageCommand
from cli_commands.status import StatusCommand
from cli_commands.menu import MenuCommand
from cli_utils.config import ConfigManager
from cli_utils.progress import ProgressManager
from cli_utils.logging import setup_cli_logging
from exceptions import BackupussyError
import argcomplete


class BackupussyCLI:
    """Main CLI application class."""
    
    def __init__(self):
        self.config_manager = None
        self.progress_manager = None
        self.logger = None
        
        # Backend managers (initialized later)
        self.dep_manager = None
        self.archive_manager = None
        self.tape_manager = None
        self.db_manager = None
        self.recovery_manager = None
        self.search_interface = None
        self.tape_library = None
        
        # Command handlers
        self.commands = {}
    
    def setup_arg_parser(self):
        """Set up the main argument parser with all commands and options."""
        parser = argparse.ArgumentParser(
            prog='backupussy',
            description='LTO Tape Backup System - Terminal Interface',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  backupussy archive create /path/to/source --device /dev/st0
  backupussy recover list --tape TAPE001
  backupussy search "*.pdf" --after 2025-01-01
  backupussy manage tapes list
  backupussy status

For detailed help on any command, use:
  backupussy COMMAND --help
"""
        )
        
        # Global options
        parser.add_argument('--version', action='version', version='%(prog)s 1.0')
        parser.add_argument('-v', '--verbose', action='count', default=0,
                          help='Increase verbosity (use -vv for debug)')
        parser.add_argument('-q', '--quiet', action='store_true',
                          help='Suppress non-error output')
        parser.add_argument('--config', type=str, metavar='FILE',
                          help='Use custom configuration file')
        parser.add_argument('--log-file', type=str, metavar='FILE',
                          help='Write logs to specified file')
        parser.add_argument('--dry-run', action='store_true',
                          help='Show what would be done without executing')
        parser.add_argument('--no-color', action='store_true',
                          help='Disable colored output')
        
        # Create subparsers for commands
        subparsers = parser.add_subparsers(
            dest='command', 
            help='Available commands',
            metavar='COMMAND'
        )
        
        # Add command parsers
        self._add_archive_parser(subparsers)
        self._add_recover_parser(subparsers)
        self._add_search_parser(subparsers)
        self._add_manage_parser(subparsers)
        self._add_status_parser(subparsers)
        self._add_menu_parser(subparsers)
        
        return parser
    
    def _add_archive_parser(self, subparsers):
        """Add archive command parser."""
        archive_parser = subparsers.add_parser('archive', help='Archive operations')
        archive_sub = archive_parser.add_subparsers(dest='archive_action', help='Archive actions')
        
        # Create subcommand
        create_parser = archive_sub.add_parser('create', help='Create new archive')
        create_parser.add_argument('source', help='Source folder to archive')
        create_parser.add_argument('--device', required=True, help='Tape device (e.g., /dev/st0 or \\.\\Tape0)')
        create_parser.add_argument('--name', help='Custom archive name')
        create_parser.add_argument('--compress', action='store_true', help='Enable compression')
        create_parser.add_argument('--copies', type=int, choices=[1, 2], default=1, help='Number of tape copies')
        create_parser.add_argument('--no-index', action='store_true', help='Skip file indexing in database')
        create_parser.add_argument('--mode', choices=['stream', 'cached'], default='cached', help='Archive mode')
        
        # Estimate subcommand
        estimate_parser = archive_sub.add_parser('estimate', help='Estimate archive size')
        estimate_parser.add_argument('source', help='Source folder to estimate')
        
        # List jobs subcommand
        list_jobs_parser = archive_sub.add_parser('list-jobs', help='List archive jobs')
        list_jobs_parser.add_argument('--active', action='store_true', help='Show only active jobs')
        
        # Cancel subcommand
        cancel_parser = archive_sub.add_parser('cancel', help='Cancel archive job')
        cancel_parser.add_argument('job_id', nargs='?', help='Job ID to cancel (if not provided, cancels current job)')
    
    def _add_recover_parser(self, subparsers):
        """Add recover command parser."""
        recover_parser = subparsers.add_parser('recover', help='Recover archives or files')
        
        # Subcommands for recover
        recover_sub = recover_parser.add_subparsers(
            dest='recover_action',
            help='Recovery actions',
            metavar='ACTION'
        )
        
        # list subcommand
        list_parser = recover_sub.add_parser('list', help='List archives available for recovery')
        list_parser.add_argument('--tape', type=str, help='Filter by tape ID')
        list_parser.add_argument('--limit', type=int, default=50, help='Max number of archives to list')
        
        # files subcommand
        files_parser = recover_sub.add_parser('files', help='List files within an archive')
        files_parser.add_argument('--archive-id', required=True, help='ID of the archive to inspect')
        files_parser.add_argument('--filter', type=str, help='Filter files by pattern')
        
        # start subcommand
        start_parser = recover_sub.add_parser('start', help='Start a recovery job')
        start_parser.add_argument('--archive-id', required=True, help='ID of the archive to recover')
        start_parser.add_argument('--destination', required=True, help='Destination directory for recovered files')
        start_parser.add_argument('files', nargs='*', help='Specific files to recover (optional, recovers all if not specified)')
        start_parser.add_argument('--overwrite', action='store_true', help='Overwrite existing files')
        start_parser.add_argument('--device', type=str, help='Specify tape device to use')
        start_parser.add_argument('--preserve-structure', action='store_true', default=True, help='Preserve directory structure')
        
        # Verify subcommand
        verify_parser = recover_sub.add_parser('verify', help='Verify archive integrity')
        verify_parser.add_argument('archive', help='Archive name or ID')
    
    def _add_search_parser(self, subparsers):
        """Add search command parser."""
        search_parser = subparsers.add_parser('search', help='Search for files across archives')
        search_parser.add_argument('query', nargs='?', help='Search query (e.g., filename pattern, part of archive name, tape label)')
        search_parser.add_argument('--entity', choices=['file', 'archive', 'tape'], default='file', help='Type of entity to search for (file, archive, tape). Default: file')
        search_parser.add_argument('--name', help='Filename pattern (Note: currently not used if positional query is provided)')
        search_parser.add_argument('--type', help='Filter by file type/extension (e.g., pdf, txt) when searching for files.')
        search_parser.add_argument('--size', help='File size (e.g., >1MB, <100KB)')
        search_parser.add_argument('--modified-after', help='Modified after date (YYYY-MM-DD)')
        search_parser.add_argument('--modified-before', help='Modified before date (YYYY-MM-DD)')
        search_parser.add_argument('--tape', help='Search specific tape')
        search_parser.add_argument('--archive', help='Search specific archive')
        search_parser.add_argument('--export', help='Export results to file')
        search_parser.add_argument('--format', choices=['table', 'csv', 'json'], default='table', help='Output format')
        search_parser.add_argument('--limit', type=int, help='Limit number of results')
    
    def _add_manage_parser(self, subparsers):
        """Add manage command parser."""
        manage_parser = subparsers.add_parser('manage', help='System and tape management')
        manage_sub = manage_parser.add_subparsers(dest='manage_action', help='Management actions')
        
        # Tapes subcommand
        tapes_parser = manage_sub.add_parser('tapes', help='Tape management')
        tapes_sub = tapes_parser.add_subparsers(dest='tapes_action', help='Tape actions')
        
        # Tape list
        tapes_list = tapes_sub.add_parser('list', help='List all tapes')
        tapes_list.add_argument('--status', help='Filter by status')
        
        # Tape add
        tapes_add = tapes_sub.add_parser('add', help='Add new tape')
        tapes_add.add_argument('--label', required=True, help='Tape label')
        tapes_add.add_argument('--device', required=True, help='Tape device')
        tapes_add.add_argument('--notes', help='Optional notes')
        
        # Tape update
        tapes_update = tapes_sub.add_parser('update', help='Update tape information')
        tapes_update.add_argument('label', help='Tape label')
        tapes_update.add_argument('--status', choices=['active', 'full', 'damaged', 'retired'], help='New status')
        tapes_update.add_argument('--notes', help='Update notes')
        
        # Tape remove
        tapes_remove = tapes_sub.add_parser('remove', help='Remove tape from inventory')
        tapes_remove.add_argument('label', help='Tape label')
        tapes_remove.add_argument('--force', action='store_true', help='Force removal without confirmation')
        
        # Devices subcommand
        devices_parser = manage_sub.add_parser('devices', help='Device management')
        devices_sub = devices_parser.add_subparsers(dest='devices_action', help='Device actions')
        
        devices_list = devices_sub.add_parser('list', help='List tape devices')
        devices_refresh = devices_sub.add_parser('refresh', help='Refresh device list')
        
        # Database subcommand
        db_parser = manage_sub.add_parser('database', help='Database operations')
        db_sub = db_parser.add_subparsers(dest='database_action', help='Database actions')
        
        db_vacuum = db_sub.add_parser('vacuum', help='Vacuum database')
        db_backup = db_sub.add_parser('backup', help='Backup database')
        db_backup.add_argument('output', help='Backup file path')
        
        db_restore = db_sub.add_parser('restore', help='Restore database')
        db_restore.add_argument('backup_file', help='Backup file to restore')
        
        # Stats subcommand
        stats_parser = manage_sub.add_parser('stats', help='Show system statistics')
        stats_parser.add_argument('--detailed', action='store_true', help='Show detailed statistics')
        
        # Config subcommand
        config_parser = manage_sub.add_parser('config', help='Configuration management')
        config_sub = config_parser.add_subparsers(dest='config_action', help='Configuration actions')

        # Config generate
        config_generate = config_sub.add_parser('generate', help='Generate a sample configuration file')
        config_generate.add_argument('--path', type=str, help='Optional path to save the configuration file. Defaults to user config directory.')
        config_generate.add_argument('--force', action='store_true', help='Overwrite if configuration file already exists at the target path.')
    
    def _add_status_parser(self, subparsers):
        """Add status command parser."""
        status_parser = subparsers.add_parser('status', help='System status and information')
        status_parser.add_argument('component', nargs='?', 
                                 choices=['devices', 'jobs', 'dependencies', 'tapes'],
                                 help='Specific component status')
        status_parser.add_argument('--watch', action='store_true', help='Watch for changes')
        
    def _add_menu_parser(self, subparsers):
        """Add menu command parser."""
        menu_parser = subparsers.add_parser('menu', help='Interactive menu system')
        menu_parser.add_argument('--mode', choices=['interactive', 'wizard'], default='interactive',
                               help='Menu mode: interactive or wizard')
    
    def initialize_managers(self, args):
        """Initialize all backend managers."""
        self.logger.info("Initializing backend managers...")

        # Initialize dependency manager first. This will raise DependencyError if not found.
        self.dep_manager = DependencyManager()
        self.dep_manager.detect_dependencies()

        # Initialize core managers
        # NOTE: In a real app, these could also raise exceptions (e.g., DB connection failed)
        self.db_manager = DatabaseManager()
        self.archive_manager = ArchiveManager(self.dep_manager, self.db_manager)
        self.tape_manager = TapeManager(self.dep_manager)
        self.recovery_manager = RecoveryManager(self.dep_manager, self.db_manager)
        self.search_interface = SearchInterface(self.db_manager, self.recovery_manager)
        self.tape_library = TapeLibrary(self.db_manager)

        self.logger.info("All backend managers initialized successfully")
    
    def initialize_commands(self):
        """Initialize command handler objects."""
        managers = {
            'dep_manager': self.dep_manager,
            'archive_manager': self.archive_manager,
            'tape_manager': self.tape_manager,
            'db_manager': self.db_manager,
            'recovery_manager': self.recovery_manager,
            'search_interface': self.search_interface,
            'tape_library': self.tape_library,
            'config_manager': self.config_manager,
            'progress_manager': self.progress_manager,
            'logger': self.logger
        }
        self.commands = {
            'archive': ArchiveCommand(managers),
            'recover': RecoverCommand(managers),
            'search': SearchCommand(managers),
            'manage': ManageCommand(managers),
            'status': StatusCommand(managers),
            'menu': MenuCommand(managers)
        }
    
    def run(self, argv=None):
        """Main CLI entry point."""
        parser = self.setup_arg_parser()
        argcomplete.autocomplete(parser) # Enable shell completion
        args = parser.parse_args(argv)
        
        # Set up configuration
        self.config_manager = ConfigManager(args.config)
        
        # Set up logging
        self.logger = setup_cli_logging(args)
        
        # Set up progress manager
        self.progress_manager = ProgressManager(args.quiet, args.no_color)
        
        # Initialize backend managers
        self.initialize_managers(args)
        
        # Initialize command handlers
        self.initialize_commands()
        
        # Handle no command provided
        if not args.command:
            parser.print_help()
            return 0
        
        # Execute command
        try:
            command_handler = self.commands.get(args.command)
            if command_handler:
                return command_handler.execute(args)
            else:
                self.logger.error(f"Unknown command: {args.command}")
                return 1
                
        except KeyboardInterrupt:
            self.logger.info("Operation cancelled by user.")
            return 130  # Standard exit code for SIGINT
        except BackupussyError as e:
            self.logger.error(f"Error: {e}")
            return 1
        except Exception as e:
            self.logger.critical(f"An unexpected error occurred: {e}")
            if args.verbose >= 2:
                import traceback
                traceback.print_exc()
            return 1


def main():
    """Entry point for the CLI application."""
    cli = BackupussyCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())

