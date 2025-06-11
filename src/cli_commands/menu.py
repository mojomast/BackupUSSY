#!/usr/bin/env python3
"""
Interactive Menu System for Backupussy CLI

Provides a user-friendly interactive interface for navigating
all backup system operations without needing to remember command syntax.
"""

import os
import sys
from typing import Dict, List, Callable, Optional
from .base import BaseCommand
from cli_utils.progress import ProgressManager
from exceptions import BackupussyError


class MenuCommand(BaseCommand):
    """Interactive menu system command."""
    
    def __init__(self, managers: Dict):
        super().__init__(managers)
        self.current_menu = 'main'
        self.menu_history = []
        
    def add_arguments(self, parser):
        """Add menu-specific arguments."""
        parser.add_argument(
            '--mode',
            choices=['interactive', 'wizard'],
            default='interactive',
            help='Menu mode: interactive (navigate freely) or wizard (guided workflows)'
        )
        
    def execute(self, args):
        """Execute the interactive menu."""
        try:
            if args.mode == 'wizard':
                self._run_wizard_mode()
            else:
                self._run_interactive_mode()
            return 0  # Success
        except KeyboardInterrupt:
            self.print_info("\n\nExiting menu system...")
            return 0
        except Exception as e:
            self.print_error(f"Menu system error: {e}")
            return 1
            
    def _run_interactive_mode(self):
        """Run the main interactive menu system."""
        self._clear_screen()
        self._show_welcome()
        
        while True:
            try:
                if self.current_menu == 'main':
                    choice = self._show_main_menu()
                elif self.current_menu == 'archive':
                    choice = self._show_archive_menu()
                elif self.current_menu == 'recover':
                    choice = self._show_recover_menu()
                elif self.current_menu == 'search':
                    choice = self._show_search_menu()
                elif self.current_menu == 'manage':
                    choice = self._show_manage_menu()
                elif self.current_menu == 'status':
                    choice = self._show_status_menu()
                else:
                    self.current_menu = 'main'
                    continue
                    
                if choice == 'quit':
                    break
                elif choice == 'back':
                    self._go_back()
                elif choice == 'main':
                    self.current_menu = 'main'
                    self.menu_history = []
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.print_error(f"Menu error: {e}")
                self._pause()
                
    def _run_wizard_mode(self):
        """Run guided wizard workflows."""
        self._clear_screen()
        self.print_header("🧙 Backupussy Setup Wizard")
        
        wizards = {
            '1': ('First-time Setup', self._wizard_first_setup),
            '2': ('Create Archive', self._wizard_create_archive),
            '3': ('Recover Files', self._wizard_recover_files),
            '4': ('Search Archives', self._wizard_search_files),
            '5': ('Tape Management', self._wizard_tape_management),
        }
        
        while True:
            print("\nAvailable Wizards:")
            for key, (name, _) in wizards.items():
                print(f"  {key}. {name}")
            print("  q. Quit")
            
            choice = input("\nSelect wizard (1-5, q): ").strip().lower()
            
            if choice == 'q':
                break
            elif choice in wizards:
                try:
                    wizards[choice][1]()
                except Exception as e:
                    self.print_error(f"Wizard error: {e}")
                finally:
                    self._pause()
            else:
                self.print_error("Invalid choice. Please try again.")
                
    def _show_welcome(self):
        """Show welcome message."""
        self.print_header("🗂️  BackupUSSY Interactive Menu")
        print("Welcome to the LTO Tape Backup System")
        print("Navigate using number keys, 'b' for back, 'm' for main menu, 'q' to quit\n")
        
    def _show_main_menu(self) -> str:
        """Show main menu and get user choice."""
        print("\n" + "="*60)
        print("MAIN MENU")
        print("="*60)
        print("1. 📦 Archive Operations  - Create and manage backups")
        print("2. 🔄 Recovery Operations - Restore files and archives")
        print("3. 🔍 Search Operations   - Find files across archives")
        print("4. ⚙️  System Management  - Manage tapes and settings")
        print("5. 📊 System Status       - View system information")
        print("6. 🧙 Wizard Mode         - Guided workflows")
        print("")
        print("q. Quit")
        
        choice = input("\nEnter your choice (1-6, q): ").strip().lower()
        
        menu_map = {
            '1': 'archive',
            '2': 'recover', 
            '3': 'search',
            '4': 'manage',
            '5': 'status',
            '6': 'wizard',
            'q': 'quit'
        }
        
        if choice in menu_map:
            if choice == '6':
                self._run_wizard_mode()
                return 'main'
            else:
                result = menu_map[choice]
                if result != 'quit':
                    self.menu_history.append(self.current_menu)
                    self.current_menu = result
                return result
        else:
            self.print_error("Invalid choice. Please try again.")
            return 'main'
            
    def _show_archive_menu(self) -> str:
        """Show archive operations menu."""
        print("\n" + "="*60)
        print("ARCHIVE OPERATIONS")
        print("="*60)
        print("1. Create New Archive     - Backup files to tape")
        print("2. Estimate Archive Size  - Calculate space needed")
        print("3. List Archive Jobs      - View active operations")
        print("4. Cancel Archive Job     - Stop running backup")
        print("")
        print("b. Back to Main Menu")
        print("q. Quit")
        
        choice = input("\nEnter your choice (1-4, b, q): ").strip().lower()
        
        if choice == '1':
            return self._handle_create_archive()
        elif choice == '2':
            return self._handle_estimate_archive()
        elif choice == '3':
            return self._handle_list_jobs()
        elif choice == '4':
            return self._handle_cancel_job()
        elif choice == 'b':
            return 'back'
        elif choice == 'q':
            return 'quit'
        else:
            self.print_error("Invalid choice. Please try again.")
            return 'archive'
            
    def _show_recover_menu(self) -> str:
        """Show recovery operations menu."""
        print("\n" + "="*60)
        print("RECOVERY OPERATIONS")
        print("="*60)
        print("1. List Available Archives - Show all backup archives")
        print("2. Browse Archive Contents - Explore files in archive")
        print("3. Extract Complete Archive - Restore full backup")
        print("4. Extract Specific Files  - Restore selected files")
        print("5. Verify Archive          - Check archive integrity")
        print("")
        print("b. Back to Main Menu")
        print("q. Quit")
        
        choice = input("\nEnter your choice (1-5, b, q): ").strip().lower()
        
        if choice == '1':
            return self._handle_list_archives()
        elif choice == '2':
            return self._handle_browse_archive()
        elif choice == '3':
            return self._handle_extract_full()
        elif choice == '4':
            return self._handle_extract_selective()
        elif choice == '5':
            return self._handle_verify_archive()
        elif choice == 'b':
            return 'back'
        elif choice == 'q':
            return 'quit'
        else:
            self.print_error("Invalid choice. Please try again.")
            return 'recover'
            
    def _show_search_menu(self) -> str:
        """Show search operations menu."""
        print("\n" + "="*60)
        print("SEARCH OPERATIONS")
        print("="*60)
        print("1. Search by Filename     - Find files by name pattern")
        print("2. Search by Content      - Find files containing text")
        print("3. Advanced Search        - Multiple criteria search")
        print("4. Search Specific Tape   - Search within one tape")
        print("5. Export Search Results  - Save results to file")
        print("")
        print("b. Back to Main Menu")
        print("q. Quit")
        
        choice = input("\nEnter your choice (1-5, b, q): ").strip().lower()
        
        if choice == '1':
            return self._handle_search_filename()
        elif choice == '2':
            return self._handle_search_content()
        elif choice == '3':
            return self._handle_search_advanced()
        elif choice == '4':
            return self._handle_search_tape()
        elif choice == '5':
            return self._handle_export_search()
        elif choice == 'b':
            return 'back'
        elif choice == 'q':
            return 'quit'
        else:
            self.print_error("Invalid choice. Please try again.")
            return 'search'
            
    def _show_manage_menu(self) -> str:
        """Show management operations menu."""
        print("\n" + "="*60)
        print("SYSTEM MANAGEMENT")
        print("="*60)
        print("1. Tape Management        - Add, update, remove tapes")
        print("2. Device Management      - Configure tape drives")
        print("3. Database Operations    - Maintain metadata")
        print("4. System Statistics      - View usage stats")
        print("5. Configuration          - System settings")
        print("")
        print("b. Back to Main Menu")
        print("q. Quit")
        
        choice = input("\nEnter your choice (1-5, b, q): ").strip().lower()
        
        if choice == '1':
            return self._handle_tape_management()
        elif choice == '2':
            return self._handle_device_management()
        elif choice == '3':
            return self._handle_database_management()
        elif choice == '4':
            return self._handle_statistics()
        elif choice == '5':
            return self._handle_configuration()
        elif choice == 'b':
            return 'back'
        elif choice == 'q':
            return 'quit'
        else:
            self.print_error("Invalid choice. Please try again.")
            return 'manage'
            
    def _show_status_menu(self) -> str:
        """Show status information menu."""
        print("\n" + "="*60)
        print("SYSTEM STATUS")
        print("="*60)
        print("1. Overall System Status  - Complete system overview")
        print("2. Device Status          - Tape drive information")
        print("3. Current Operations     - Active jobs and tasks")
        print("4. Dependency Check       - External tool status")
        print("5. Database Status        - Metadata information")
        print("")
        print("b. Back to Main Menu")
        print("q. Quit")
        
        choice = input("\nEnter your choice (1-5, b, q): ").strip().lower()
        
        if choice == '1':
            return self._handle_system_status()
        elif choice == '2':
            return self._handle_device_status()
        elif choice == '3':
            return self._handle_operations_status()
        elif choice == '4':
            return self._handle_dependency_status()
        elif choice == '5':
            return self._handle_database_status()
        elif choice == 'b':
            return 'back'
        elif choice == 'q':
            return 'quit'
        else:
            self.print_error("Invalid choice. Please try again.")
            return 'status'
            
    def _go_back(self):
        """Go back to previous menu."""
        if self.menu_history:
            self.current_menu = self.menu_history.pop()
        else:
            self.current_menu = 'main'
            
    def _clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def _pause(self):
        """Pause and wait for user input."""
        input("\nPress Enter to continue...")
        
    # Archive operation handlers
    def _handle_create_archive(self) -> str:
        """Handle archive creation through interactive prompts."""
        try:
            print("\n📦 CREATE NEW ARCHIVE")
            print("="*40)
            
            # Get source directory
            source = input("Enter source directory path: ").strip()
            if not source:
                self.print_error("Source directory is required.")
                self._pause()
                return 'archive'
                
            if not os.path.exists(source):
                self.print_error(f"Source directory does not exist: {source}")
                self._pause()
                return 'archive'
                
            # Get archive name (optional)
            name = input("Enter archive name (optional, press Enter for auto): ").strip()
            
            # Get compression option
            compress = input("Enable compression? (y/N): ").strip().lower()
            compress = compress in ['y', 'yes']
            
            # Get tape device
            device = input("Enter tape device (e.g., /dev/st0) or press Enter for auto: ").strip()
            
            # Auto-detect device if none provided
            if not device:
                try:
                    # Try to get available devices from tape manager
                    if 'tape_manager' in self.managers and self.managers['tape_manager']:
                        devices = self.managers['tape_manager'].detect_tape_devices()
                        if devices:
                            device = devices[0]  # Use first available device
                            self.print_info(f"Auto-detected device: {device}")
                        else:
                            self.print_error("No tape devices detected on this system.")
                            self.print_info("Please connect a tape drive or use --dry-run mode for testing.")
                            self._pause()
                            return 'archive'
                    else:
                        self.print_error("Tape manager not available.")
                        self._pause()
                        return 'archive'
                except Exception as e:
                    self.print_error(f"Device detection failed: {e}")
                    self._pause()
                    return 'archive'
            
            # Get number of copies
            copies_str = input("Number of tape copies (1-2, default 1): ").strip()
            try:
                copies = int(copies_str) if copies_str else 1
                if copies not in [1, 2]:
                    raise ValueError()
            except ValueError:
                self.print_error("Invalid number of copies. Using default (1).")
                copies = 1
                
            # Confirm operation
            print(f"\nArchive Configuration:")
            print(f"  Source: {source}")
            print(f"  Name: {name or 'Auto-generated'}")
            print(f"  Compression: {'Yes' if compress else 'No'}")
            print(f"  Device: {device or 'Auto-detect'}")
            print(f"  Copies: {copies}")
            
            confirm = input("\nProceed with archive creation? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                self.print_info("Archive creation cancelled.")
                self._pause()
                return 'archive'
                
            # Execute archive creation
            self.print_info("\nStarting archive creation...")
            
            # Import and use the actual archive command
            from .archive import ArchiveCommand
            archive_cmd = ArchiveCommand(self.managers)
            
            # Build arguments for archive creation
            class Args:
                def __init__(self):
                    self.archive_action = 'create'
                    self.source = source
                    self.name = name if name else None
                    self.compress = compress
                    self.device = device if device else None
                    self.copies = copies
                    self.verbose = False
                    self.quiet = False
                    
            args = Args()
            result = archive_cmd.execute(args)
            
            if result == 0:
                self.print_success("Archive created successfully!")
            else:
                self.print_error("Archive creation failed.")
                
        except Exception as e:
            self.print_error(f"Error creating archive: {e}")
            
        self._pause()
        return 'archive'
        
    def _handle_estimate_archive(self) -> str:
        """Handle archive size estimation."""
        try:
            print("\n📊 ESTIMATE ARCHIVE SIZE")
            print("="*40)
            
            source = input("Enter source directory path: ").strip()
            if not source:
                self.print_error("Source directory is required.")
                self._pause()
                return 'archive'
                
            if not os.path.exists(source):
                self.print_error(f"Source directory does not exist: {source}")
                self._pause()
                return 'archive'
                
            compress = input("Include compression in estimate? (y/N): ").strip().lower()
            compress = compress in ['y', 'yes']
            
            self.print_info("\nCalculating archive size...")
            
            # Import and use the actual archive command
            from .archive import ArchiveCommand
            archive_cmd = ArchiveCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.archive_action = 'estimate'  # For ArchiveCommand.execute
                    self.source = source              # Expected by _estimate_archive
                    self.compression = compress       # Argument name used in ArchiveCommand
                    self.name = None                  # Not strictly needed for estimate, but good for consistency
                    self.description = None
                    self.tags = None
                    self.tape_label = None
                    self.encryption_key = None
                    self.mode = None
                    self.verify = False
                    self.skip_estimation = True       # Already estimating, no need to re-estimate
                    
            args = Args()
            archive_cmd.execute(args)
            
        except Exception as e:
            self.print_error(f"Error estimating archive size: {e}")
            
        self._pause()
        return 'archive'
        
    def _handle_list_jobs(self) -> str:
        """Handle listing archive jobs."""
        try:
            print("\n📋 ACTIVE ARCHIVE JOBS")
            print("="*40)
            
            from .archive import ArchiveCommand
            archive_cmd = ArchiveCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.archive_action = 'jobs'  # For ArchiveCommand.execute
                    
            args = Args()
            archive_cmd.execute(args)
            
        except Exception as e:
            self.print_error(f"Error listing jobs: {e}")
            
        self._pause()
        return 'archive'
        
    def _handle_cancel_job(self) -> str:
        """Handle cancelling archive jobs."""
        try:
            print("\n❌ CANCEL ARCHIVE JOB")
            print("="*40)
            
            job_id = input("Enter job ID to cancel: ").strip()
            if not job_id:
                self.print_error("Job ID is required.")
                self._pause()
                return 'archive'
                
            confirm = input(f"Cancel job {job_id}? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                self.print_info("Job cancellation aborted.")
                self._pause()
                return 'archive'
                
            from .archive import ArchiveCommand
            archive_cmd = ArchiveCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.archive_action = 'cancel'  # For ArchiveCommand.execute
                    self.job_id = job_id
                    
            args = Args()
            result = archive_cmd.execute(args)
            
            if result == 0:
                self.print_success(f"Job {job_id} cancelled successfully.")
            else:
                self.print_error(f"Failed to cancel job {job_id}.")
                
        except Exception as e:
            self.print_error(f"Error cancelling job: {e}")
            
        self._pause()
        return 'archive'
        
    # Recovery operation handlers
    def _handle_list_archives(self) -> str:
        """Handle listing available archives."""
        try:
            print("\n📚 AVAILABLE ARCHIVES")
            print("="*40)
            
            tape_filter = input("Filter by tape (optional, press Enter for all): ").strip()
        
            from .archive import ArchiveCommand
            archive_cmd = ArchiveCommand(self.managers)
        
            class Args:
                def __init__(self):
                    self.archive_action = 'list'  # For ArchiveCommand.execute
                    self.tape = tape_filter if tape_filter else None
                    self.limit = 50 # Default limit, similar to CLI
                
            args = Args()
            archive_cmd.execute(args)
        
        except Exception as e:
            self.print_error(f"Error listing archives: {e}")
        
        self._pause()
        return 'recover'
        
    def _handle_browse_archive(self) -> str:
        """Handle browsing archive contents."""
        try:
            print("\n🔍 BROWSE ARCHIVE CONTENTS")
            print("="*40)
            
            archive = input("Enter archive name/ID: ").strip()
            if not archive:
                self.print_error("Archive name is required.")
                self._pause()
                return 'recover'
                
            from .recover import RecoverCommand
            recover_cmd = RecoverCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.recover_action = 'files'  # For RecoverCommand.execute, maps to _list_files
                    self.archive_id = archive    # Parameter expected by _list_files
                    self.filter = None           # Optional: not prompting for filter in menu
                    
            args = Args()
            recover_cmd.execute(args)
            
        except Exception as e:
            self.print_error(f"Error browsing archive: {e}")
            
        self._pause()
        return 'recover'
        
    def _handle_extract_full(self) -> str:
        """Handle full archive extraction."""
        try:
            print("\n📤 EXTRACT COMPLETE ARCHIVE")
            print("="*40)
            
            archive = input("Enter archive name/ID: ").strip()
            if not archive:
                self.print_error("Archive name is required.")
                self._pause()
                return 'recover'
                
            output = input("Enter output directory: ").strip()
            if not output:
                self.print_error("Output directory is required.")
                self._pause()
                return 'recover'
                
            verify = input("Verify extraction? (Y/n): ").strip().lower()
            verify = verify not in ['n', 'no']
            
            print(f"\nExtraction Configuration:")
            print(f"  Archive: {archive}")
            print(f"  Output: {output}")
            print(f"  Verify: {'Yes' if verify else 'No'}")
            
            confirm = input("\nProceed with extraction? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                self.print_info("Extraction cancelled.")
                self._pause()
                return 'recover'
            
            from .recover import RecoverCommand
            recover_cmd = RecoverCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.recover_action = 'archive'  # For RecoverCommand.execute, maps to _recover_archive
                    self.archive_id = archive        # Parameter expected by _recover_archive
                    self.destination_path = output   # Parameter expected by _recover_archive
                    self.verify = verify
                    self.tape_label = None         # Optional: not prompting for in menu
                    self.encryption_key = None     # Optional: not prompting for in menu
                    self.files = None              # For full archive extraction
                    self.force = False             # Using manual confirmation in menu
                    
            args = Args()
            result = recover_cmd.execute(args)
            
            if result == 0:
                self.print_success("Archive extracted successfully!")
            else:
                self.print_error("Archive extraction failed.")
                
        except Exception as e:
            self.print_error(f"Error extracting archive: {e}")
            
        self._pause()
        return 'recover'
        
    def _handle_extract_selective(self) -> str:
        """Handle selective file extraction."""
        try:
            print("\n📤 EXTRACT SPECIFIC FILES")
            print("="*40)
            
            archive = input("Enter archive name/ID: ").strip()
            if not archive:
                self.print_error("Archive name is required.")
                self._pause()
                return 'recover'
                
            files = input("Enter file patterns (space-separated): ").strip()
            if not files:
                self.print_error("File patterns are required.")
                self._pause()
                return 'recover'
                
            output = input("Enter output directory: ").strip()
            if not output:
                self.print_error("Output directory is required.")
                self._pause()
                return 'recover'
                
            print(f"\nSelective Extraction Configuration:")
            print(f"  Archive: {archive}")
            print(f"  Files: {files}")
            print(f"  Output: {output}")
            
            confirm = input("\nProceed with extraction? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                self.print_info("Extraction cancelled.")
                self._pause()
                return 'recover'
                
            from .recover import RecoverCommand
            recover_cmd = RecoverCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.recover_action = 'archive'  # For RecoverCommand.execute, maps to _recover_archive
                    self.archive_id = archive        # Parameter expected by _recover_archive
                    self.files = files.split()       # List of files/patterns to extract
                    self.destination_path = output   # Parameter expected by _recover_archive
                    self.tape_label = None         # Optional: not prompting for in menu
                    self.encryption_key = None     # Optional: not prompting for in menu
                    self.verify = False            # Optional: not prompting for in menu
                    self.force = False             # Using manual confirmation in menu
                    
            args = Args()
            result = recover_cmd.execute(args)
            
            if result == 0:
                self.print_success("Files extracted successfully!")
            else:
                self.print_error("File extraction failed.")
                
        except Exception as e:
            self.print_error(f"Error extracting files: {e}")
            
        self._pause()
        return 'recover'
        
    def _handle_verify_archive(self) -> str:
        """Handle archive verification."""
        try:
            print("\n✅ VERIFY ARCHIVE INTEGRITY")
            print("="*40)
            
            archive = input("Enter archive name/ID: ").strip()
            if not archive:
                self.print_error("Archive name is required.")
                self._pause()
                return 'recover'
                
            from .recover import RecoverCommand
            recover_cmd = RecoverCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.recover_action = 'verify'  # For RecoverCommand.execute, maps to _verify_archive
                    self.archive_id = archive       # Parameter expected by _verify_archive
                    self.tape_label = None        # Optional: not prompting for in menu
                    self.force = False            # Using manual confirmation in menu
                    
            args = Args()
            result = recover_cmd.execute(args)
            
            if result == 0:
                self.print_success("Archive verification completed!")
            else:
                self.print_error("Archive verification failed.")
                
        except Exception as e:
            self.print_error(f"Error verifying archive: {e}")
            
        self._pause()
        return 'recover'
        
    # Search operation handlers
    def _handle_search_filename(self) -> str:
        """Handle filename search."""
        try:
            print("\n🔍 SEARCH BY FILENAME")
            print("="*40)
            
            pattern = input("Enter filename pattern (supports wildcards): ").strip()
            if not pattern:
                self.print_error("Filename pattern is required.")
                self._pause()
                return 'search'
                
            from .search import SearchCommand
            search_cmd = SearchCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.query = None      # Positional query, not used for specific filename search via menu
                    self.name = pattern    # Specific filename pattern search
                    self.content = None
                    self.tape = None
                    self.after = None
                    self.before = None
                    self.size = None
                    self.export = None
                    
            args = Args()
            search_cmd.execute(args)
            
        except Exception as e:
            self.print_error(f"Error searching files: {e}")
            
        self._pause()
        return 'search'
        
    def _handle_search_content(self) -> str:
        """Handle content search."""
        try:
            print("\n🔍 SEARCH BY CONTENT")
            print("="*40)
            
            content = input("Enter content to search for: ").strip()
            if not content:
                self.print_error("Content search term is required.")
                self._pause()
                return 'search'
                
            from .search import SearchCommand
            search_cmd = SearchCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.query = None      # Positional query, not used for specific content search via menu
                    self.name = None
                    self.content = content # Specific content search pattern
                    self.tape = None
                    self.after = None
                    self.before = None
                    self.size = None
                    self.export = None
                    
            args = Args()
            search_cmd.execute(args)
            
        except Exception as e:
            self.print_error(f"Error searching content: {e}")
            
        self._pause()
        return 'search'
        
    def _handle_search_advanced(self) -> str:
        """Handle advanced multi-criteria search."""
        try:
            print("\n🔍 ADVANCED SEARCH")
            print("="*40)
            
            name = input("Filename pattern (optional): ").strip() or None
            content = input("Content search (optional): ").strip() or None
            tape = input("Tape filter (optional): ").strip() or None
            after = input("After date (YYYY-MM-DD, optional): ").strip() or None
            before = input("Before date (YYYY-MM-DD, optional): ").strip() or None
            size = input("Size filter (e.g., >1MB, <100KB, optional): ").strip() or None
            
            if not any([name, content, tape, after, before, size]):
                self.print_error("At least one search criterion is required.")
                self._pause()
                return 'search'
                
            print(f"\nSearch Configuration:")
            if name: print(f"  Filename: {name}")
            if content: print(f"  Content: {content}")
            if tape: print(f"  Tape: {tape}")
            if after: print(f"  After: {after}")
            if before: print(f"  Before: {before}")
            if size: print(f"  Size: {size}")
            
            confirm = input("\nProceed with search? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                self.print_info("Search cancelled.")
                self._pause()
                return 'search'
                
            from .search import SearchCommand
            search_cmd = SearchCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.query = None      # Positional query, not used for advanced search via menu
                    self.name = name
                    self.content = content
                    self.tape = tape
                    self.after = after
                    self.before = before
                    self.size = size
                    self.export = None # Not handling export in this menu option directly
                    
            args = Args()
            search_cmd.execute(args)
            
        except Exception as e:
            self.print_error(f"Error performing advanced search: {e}")
            
        self._pause()
        return 'search'
        
    def _handle_search_tape(self) -> str:
        """Handle tape-specific search."""
        try:
            print("\n🔍 SEARCH SPECIFIC TAPE")
            print("="*40)
            
            tape = input("Enter tape label/ID: ").strip()
            if not tape:
                self.print_error("Tape label is required.")
                self._pause()
                return 'search'
                
            pattern = input("Enter filename pattern (optional, * for all): ").strip()
            if not pattern:
                pattern = "*"
                
            from .search import SearchCommand
            search_cmd = SearchCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.query = None      # Positional query, not used when tape and optional name are specified
                    self.name = pattern if pattern != "*" else None
                    self.content = None
                    self.tape = tape
                    self.after = None
                    self.before = None
                    self.size = None
                    self.export = None
                    
            args = Args()
            search_cmd.execute(args)
            
        except Exception as e:
            self.print_error(f"Error searching tape: {e}")
            
        self._pause()
        return 'search'
        
    def _handle_export_search(self) -> str:
        """Handle search result export."""
        try:
            print("\n📁 EXPORT SEARCH RESULTS")
            print("="*40)
            
            # First perform a search
            pattern = input("Enter search pattern: ").strip()
            if not pattern:
                self.print_error("Search pattern is required.")
                self._pause()
                return 'search'
                
            output_file = input("Enter output filename (.csv): ").strip()
            if not output_file:
                self.print_error("Output filename is required.")
                self._pause()
                return 'search'
                
            if not output_file.endswith('.csv'):
                output_file += '.csv'
                
            from .search import SearchCommand
            search_cmd = SearchCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.query = pattern   # General search query
                    self.name = None       # Not specifically a filename search from this prompt
                    self.content = None    # Not specifically a content search from this prompt
                    self.tape = None
                    self.after = None
                    self.before = None
                    self.size = None
                    self.export = output_file
                    
            args = Args()
            result = search_cmd.execute(args)
            
            if result == 0:
                self.print_success(f"Search results exported to {output_file}")
            else:
                self.print_error("Failed to export search results.")
                
        except Exception as e:
            self.print_error(f"Error exporting search results: {e}")
            
        self._pause()
        return 'search'
        
    # Management operation handlers
    def _handle_tape_management(self) -> str:
        """Handle tape management operations."""
        try:
            print("\n🗂️  TAPE MANAGEMENT")
            print("="*40)
            
            operations = {
                '1': 'List all tapes',
                '2': 'Add new tape', 
                '3': 'Update tape status',
                '4': 'Remove tape',
                '5': 'Get tape info'
            }
            
            for key, desc in operations.items():
                print(f"  {key}. {desc}")
                
            choice = input("\nEnter choice (1-5): ").strip()
            
            from .manage import ManageCommand
            manage_cmd = ManageCommand(self.managers)
            
            if choice == '1':  # List tapes
                class Args:
                    def __init__(self):
                        self.manage_action = 'tapes'
                        self.tape_action = 'list'
                        
                args = Args()
                manage_cmd.execute(args)
                
            elif choice == '2':
                label = input("Enter tape label: ").strip()
                device = input("Enter device path (optional): ").strip() or None
                
                class Args:
                    def __init__(self):
                        self.manage_action = 'tapes'
                        self.tape_action = 'add'
                        self.label = label
                        self.device = device
                        self.size = None # Not prompted in menu
                        self.status = None # Defaults in ManageCommand
                        
                args = Args()
                manage_cmd.execute(args)
                
            elif choice == '3':
                label = input("Enter tape label: ").strip()
                status = input("Enter new status (active/full/damaged/retired): ").strip()
                
                class Args:
                    def __init__(self):
                        self.manage_action = 'tapes'
                        self.tape_action = 'update'
                        self.label = label
                        self.status = status
                        self.new_label = None # Not prompted in menu
                        self.device = None # Not prompted in menu
                        
                args = Args()
                manage_cmd.execute(args)
                
            elif choice == '4':
                label = input("Enter tape label to remove: ").strip()
                confirm = input(f"Remove tape {label}? (y/N): ").strip().lower()
                
                if confirm in ['y', 'yes']:
                    class Args:
                        def __init__(self):
                            self.manage_action = 'tapes'
                            self.tape_action = 'remove'
                            self.label = label
                            
                    args = Args()
                    manage_cmd.execute(args)
                else:
                    self.print_info("Tape removal cancelled.")
                    
            elif choice == '5':
                label = input("Enter tape label: ").strip()
                
                class Args:
                    def __init__(self):
                        self.manage_action = 'tapes'
                        self.tape_action = 'info'
                        self.label = label
                        
                args = Args()
                manage_cmd.execute(args)
                
            else:
                self.print_error("Invalid choice.")
                
        except Exception as e:
            self.print_error(f"Error in tape management: {e}")
            
        self._pause()
        return 'manage'
        
    def _handle_device_management(self) -> str:
        """Handle device management operations."""
        try:
            print("\n🖥️  DEVICE MANAGEMENT")
            print("="*40)
            
            from .manage import ManageCommand
            manage_cmd = ManageCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.manage_action = 'devices'
                    self.device_action = 'list'
                    
            args = Args()
            manage_cmd.execute(args)
            
        except Exception as e:
            self.print_error(f"Error in device management: {e}")
            
        self._pause()
        return 'manage'
        
    def _handle_database_management(self) -> str:
        """Handle database management operations."""
        try:
            print("\n🗄️  DATABASE MANAGEMENT")
            print("="*40)
            
            operations = {
                '1': 'Vacuum database',
                '2': 'Check database integrity',
                '3': 'Backup database',
                '4': 'Show database statistics'
            }
            
            for key, desc in operations.items():
                print(f"  {key}. {desc}")
                
            choice = input("\nEnter choice (1-4): ").strip()
            
            from .manage import ManageCommand
            manage_cmd = ManageCommand(self.managers)
            
            action_map = {
                '1': 'vacuum',
                '2': 'check', 
                '3': 'backup',
                '4': 'stats'
            }
            
            if choice in action_map:
                class Args:
                    def __init__(self):
                        self.manage_action = 'database'
                        self.db_action = action_map[choice]
                        # For 'backup', a 'path' argument might be needed if not using a default
                        # For 'stats', it might take optional 'table_name' etc.
                        # These are not prompted in the current menu logic.
                        
                args = Args()
                manage_cmd.execute(args)
            else:
                self.print_error("Invalid choice.")
                
        except Exception as e:
            self.print_error(f"Error in database management: {e}")
            
        self._pause()
        return 'manage'
        
    def _handle_statistics(self) -> str:
        """Handle system statistics display."""
        try:
            print("\n📊 SYSTEM STATISTICS")
            print("="*40)
            
            from .manage import ManageCommand
            manage_cmd = ManageCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.manage_action = 'stats'
                    # Optional: self.detail_level or specific stats sections if supported by ManageCommand
                    # Not prompted in the current menu logic.
                    
            args = Args()
            manage_cmd.execute(args)
            
        except Exception as e:
            self.print_error(f"Error displaying statistics: {e}")
            
        self._pause()
        return 'manage'

    def _handle_configuration(self) -> str:
        """Handle configuration management."""
        try:
            print("\n⚙️  CONFIGURATION MANAGEMENT")
            print("="*40)
            
            operations = {
                '1': 'Generate configuration template',
                '2': 'View current configuration',
                '3': 'Edit configuration'
            }
            
            for key, desc in operations.items():
                print(f"  {key}. {desc}")
                
            choice = input("\nEnter choice (1-3): ").strip()
            
            from .manage import ManageCommand
            manage_cmd = ManageCommand(self.managers)
            
            if choice == '1': # Generate config
                class Args:
                    def __init__(self):
                        self.manage_action = 'config'
                        self.config_action = 'generate'
                        self.path = None # Optional path, not prompted here
                args = Args()
                manage_cmd.execute(args)
                
            elif choice == '2': # Show config
                class Args:
                    def __init__(self):
                        self.manage_action = 'config'
                        self.config_action = 'show'
                        self.path = None # Optional path, not prompted here
                args = Args()
                manage_cmd.execute(args)
                
            elif choice == '3': # Edit configuration (manual instruction)
                self.print_info("Use your preferred text editor to edit the configuration file.")
                config_file = input("Enter config file path (or press Enter for default): ").strip()
                if not config_file:
                    try:
                        default_config_path = self.managers.config.get_config_file_path()
                        self.print_info(f"Default configuration file is typically at: {default_config_path}")
                        config_file = default_config_path
                    except Exception:
                        config_file = "backupussy.conf" # Fallback default
                self.print_info(f"Please edit '{config_file}' and restart the application if necessary.")
                
            else:
                self.print_error("Invalid choice.")
                
        except Exception as e:
            self.print_error(f"Error in configuration management: {e}")
        self._pause()
        return 'manage'

    # Status operation handlers
    def _handle_system_status(self) -> str:
        """Handle overall system status display."""
        try:
            print("\n📊 SYSTEM STATUS OVERVIEW")
            print("="*40)
            
            from .status import StatusCommand
            status_cmd = StatusCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.status_action = None # Or 'overview', assuming None implies general system status
                    
            args = Args()
            status_cmd.execute(args)
            
        except Exception as e:
            self.print_error(f"Error getting system status: {e}")
            
        self._pause()
        return 'status'
        
    def _handle_device_status(self) -> str:
        """Handle device status display."""
        try:
            print("\n🖥️  DEVICE STATUS")
            print("="*40)
            
            from .status import StatusCommand
            status_cmd = StatusCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.status_action = 'devices'
                    
            args = Args()
            status_cmd.execute(args)
            
        except Exception as e:
            self.print_error(f"Error getting device status: {e}")
            
        self._pause()
        return 'status'
        
    def _handle_operations_status(self) -> str:
        """Handle current operations status."""
        try:
            print("\n⚡ CURRENT OPERATIONS")
            print("="*40)
            
            from .status import StatusCommand
            status_cmd = StatusCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.status_action = 'jobs'
                    
            args = Args()
            status_cmd.execute(args)
            
        except Exception as e:
            self.print_error(f"Error getting operations status: {e}")
            
        self._pause()
        return 'status'
        
    def _handle_dependency_status(self) -> str:
        """Handle dependency status check."""
        try:
            print("\n🔧 DEPENDENCY STATUS")
            print("="*40)
            
            from .status import StatusCommand
            status_cmd = StatusCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.status_action = 'dependencies'
                    
            args = Args()
            status_cmd.execute(args)
            
        except Exception as e:
            self.print_error(f"Error checking dependencies: {e}")
            
        self._pause()
        return 'status'
        
    def _handle_database_status(self) -> str:
        """Handle database status display."""
        try:
            print("\n🗄️  DATABASE STATUS")
            print("="*40)
            
            from .status import StatusCommand
            status_cmd = StatusCommand(self.managers)
            
            class Args:
                def __init__(self):
                    self.status_action = 'database'
                    
            args = Args()
            status_cmd.execute(args)
            
        except Exception as e:
            self.print_error(f"Error getting database status: {e}")
            
        self._pause()
        return 'status'
        
    # Wizard implementations
    def _wizard_first_setup(self):
        """First-time setup wizard."""
        print("\n🧙 FIRST-TIME SETUP WIZARD")
        print("="*50)
        print("This wizard will help you configure Backupussy for first use.\n")
        
        # Check dependencies
        print("1. Checking system dependencies...")
        from .status import StatusCommand
        status_cmd = StatusCommand(self.managers)
        
        class Args:
            def __init__(self):
                self.status_action = 'dependencies'
                
        args = Args()
        status_cmd.execute(args)
        
        # Check for tape devices
        print("\n2. Checking for tape devices...")
        args.status_action = 'devices'
        status_cmd.execute(args)
        
        # Generate configuration
        print("\n3. Generating configuration template...")
        from .manage import ManageCommand
        manage_cmd = ManageCommand(self.managers)
        
        class ConfigArgs:
            def __init__(self):
                self.manage_action = 'config'    # For ManageCommand.execute
                self.config_action = 'generate'  # For ManageCommand._handle_config_management
                self.path = None                 # For ManageCommand._generate_config_file (use default path)
                self.force = False               # For ManageCommand._generate_config_file (do not force overwrite)
                
        config_args = ConfigArgs()
        manage_cmd.execute(config_args)
        
        print("\n✅ First-time setup completed!")
        print("Edit 'backupussy.conf' to customize your settings.")
        
    def _wizard_create_archive(self):
        """Archive creation wizard."""
        print("\n🧙 ARCHIVE CREATION WIZARD")
        print("="*50)
        
        # Step-by-step archive creation with validation
        self._handle_create_archive()
        
    def _wizard_recover_files(self):
        """File recovery wizard."""
        print("\n🧙 FILE RECOVERY WIZARD")
        print("="*50)
        
        # Step 1: List archives
        print("Step 1: Available archives")
        self._handle_list_archives()
        
        # Step 2: Choose recovery type
        print("\nStep 2: Choose recovery type")
        print("1. Recover complete archive")
        print("2. Recover specific files")
        
        choice = input("Enter choice (1-2): ").strip()
        
        if choice == '1':
            self._handle_extract_full()
        elif choice == '2':
            self._handle_extract_selective()
        else:
            self.print_error("Invalid choice.")
            
    def _wizard_search_files(self):
        """File search wizard."""
        print("\n🧙 FILE SEARCH WIZARD")
        print("="*50)
        
        # Step-by-step search with suggestions
        print("What would you like to search for?")
        print("1. Find files by name")
        print("2. Find files containing specific text")
        print("3. Find files on a specific tape")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            self._handle_search_filename()
        elif choice == '2':
            self._handle_search_content()
        elif choice == '3':
            self._handle_search_tape()
        else:
            self.print_error("Invalid choice.")
            
    def _wizard_tape_management(self):
        """Tape management wizard."""
        print("\n🧙 TAPE MANAGEMENT WIZARD")
        print("="*50)
        
        # Step-by-step tape management
        print("What would you like to do?")
        print("1. Add a new tape")
        print("2. Update tape status")
        print("3. View tape information")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            print("\nAdding a new tape...")
            label = input("Enter tape label (e.g., TAPE001): ").strip()
            
            if label:
                from .manage import ManageCommand
                manage_cmd = ManageCommand(self.managers)
                
                class Args:
                    def __init__(self):
                        self.manage_action = 'tapes'
                        self.tape_action = 'add'
                        self.label = label
                        self.device = None
                        
                args = Args()
                result = manage_cmd.execute(args)
                
                if result == 0:
                    self.print_success(f"Tape {label} added successfully!")
                else:
                    self.print_error(f"Failed to add tape {label}.")
            else:
                self.print_error("Tape label is required.")
                
        elif choice in ['2', '3']:
            # Delegate to existing handlers
            if choice == '2':
                print("\nUpdating tape status...")
            else:
                print("\nViewing tape information...")
                
            self._handle_tape_management()
        else:
            self.print_error("Invalid choice.")

