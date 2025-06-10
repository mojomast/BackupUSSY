#!/usr/bin/env python3
"""
BackupUSSY - Professional LTO Tape Archive Tool
GUI Application using FreeSimpleGUI interface
"""

import os
import threading
import time
import logging
from pathlib import Path

try:
    import FreeSimpleGUI as sg
except ImportError:
    print("FreeSimpleGUI not installed. Please run: pip install FreeSimpleGUI")
    exit(1)

from version import *
from main import DependencyManager
from archive_manager import ArchiveManager
from tape_manager import TapeManager
from logger_manager import LoggerManager
from database_manager import DatabaseManager
from recovery_manager import RecoveryManager
from search_interface import SearchInterface
from advanced_search import AdvancedSearchManager, AdvancedSearchGUI
from tape_browser import TapeBrowser

# Configure FreeSimpleGUI theme
sg.theme('DarkBlue3')

class LTOArchiveGUI:
    """Main GUI application for LTO tape archiving."""
    
    def __init__(self):
        self.dep_manager = None
        self.archive_manager = None
        self.tape_manager = None
        self.logger_manager = None
        self.db_manager = None
        self.recovery_manager = None
        self.search_interface = None
        self.advanced_search = None
        self.tape_browser = None
        
        self.window = None
        self.current_job = None
        self.job_thread = None
        
        # Setup logging
        self.setup_logging()
        
        # Initialize managers
        self.initialize_managers()
        
        # Create enhanced GUI with tabs
        self.create_main_gui()
        
    def create_main_gui(self):
        """Create the main GUI window with tabbed interface."""
        # Create all tabs
        archive_tab = self.create_archive_tab()
        recovery_tab = self.create_recovery_tab()
        search_tab = self.create_search_tab()
        manage_tab = self.create_management_tab()
        
        # Main tabbed layout
        layout = [
            [sg.TabGroup([
                [sg.Tab('Archive', archive_tab, key='-TAB_ARCHIVE-')],
                [sg.Tab('Recovery', recovery_tab, key='-TAB_RECOVERY-')],
                [sg.Tab('Search', search_tab, key='-TAB_SEARCH-')],
                [sg.Tab('Management', manage_tab, key='-TAB_MANAGE-')]
            ], expand_x=True, expand_y=True)],
            [sg.StatusBar(READY_MESSAGE, key='-MAIN_STATUS-', size=(80, 1))],
            [sg.Button('Exit', key='-EXIT-', size=(10, 1))]
        ]
        
        self.window = sg.Window(
            MAIN_WINDOW_TITLE,
            layout,
            size=(1200, 800),
            resizable=True,
            finalize=True
        )
        
        # Initial status update
        self.update_tape_status()
    
    def create_archive_tab(self):
        """Create the archiving tab layout."""
        # Source folder selection
        folder_frame = [
            [sg.Text('Source Folder:', size=(12, 1)), 
             sg.Input(key='-FOLDER-', size=(50, 1)), 
             sg.FolderBrowse()],
            [sg.Text('Estimated Size:', size=(12, 1)), 
             sg.Text('Not calculated', key='-SIZE-', size=(30, 1)),
             sg.Button('Calculate Size', key='-CALC_SIZE-')]
        ]
        
        # Tape device selection
        devices = self.tape_manager.detect_tape_devices()
        if not devices:
            devices = ['\\.\\Tape0']  # Default even if not detected
        
        device_frame = [
            [sg.Text('Tape Device:', size=(12, 1)), 
             sg.Combo(devices, default_value=devices[0], key='-DEVICE-', size=(20, 1)),
             sg.Button('Refresh Devices', key='-REFRESH-')],
            [sg.Text('Tape Status:', size=(12, 1)), 
             sg.Text('Unknown', key='-TAPE_STATUS-', size=(30, 1))],
            [sg.Text('Suggested Tape:', size=(12, 1)), 
             sg.Text('None selected', key='-SUGGESTED_TAPE-', size=(30, 1))]
        ]
        
        # Archive options
        options_frame = [
            [sg.Text('Archive Mode:', size=(12, 1)),
             sg.Radio('Stream to Tape', 'MODE', key='-STREAM-', default=True),
             sg.Radio('Cache & Write', 'MODE', key='-CACHED-')],
            [sg.Text('Copies:', size=(12, 1)),
             sg.Radio('1 Tape', 'COPIES', key='-COPY1-', default=True),
             sg.Radio('2 Tapes', 'COPIES', key='-COPY2-')],
            [sg.Checkbox('Compression', key='-COMPRESS-', default=True),
             sg.Checkbox('Create Database Index', key='-INDEX_FILES-', default=True)],
            [sg.Text('Archive Name:', size=(12, 1)),
             sg.Input(key='-ARCHIVE_NAME-', size=(30, 1)),
             sg.Text('(auto-generated if empty)')]
        ]
        
        # Progress and logging
        progress_frame = [
            [sg.Text('Progress:'), sg.ProgressBar(100, key='-PROGRESS-', size=(50, 20))],
            [sg.Text('Status:', size=(8, 1)), sg.Text('Ready', key='-STATUS-', size=(60, 1))],
            [sg.Multiline(size=(100, 12), key='-LOG-', disabled=True, autoscroll=True)]
        ]
        
        # Control buttons
        button_frame = [
            [sg.Button('Start Archive', key='-START-', size=(12, 1)),
             sg.Button('Cancel', key='-CANCEL-', size=(12, 1), disabled=True),
             sg.Button('Preview Files', key='-PREVIEW-', size=(12, 1))]
        ]
        
        return [
            [sg.Frame('Source Folder', folder_frame, expand_x=True)],
            [sg.Frame('Tape Device', device_frame, expand_x=True)],
            [sg.Frame('Archive Options', options_frame, expand_x=True)],
            [sg.Frame('Progress', progress_frame, expand_x=True, expand_y=True)],
            [sg.Frame('Controls', button_frame, expand_x=True)]
        ]
    
    def create_recovery_tab(self):
        """Create the recovery tab layout."""
        # Tape selection for recovery
        tape_select_frame = [
            [sg.Text('Recovery Source:', font=('Arial', 10, 'bold'))],
            [sg.Text('Tape:', size=(10, 1)),
             sg.Combo([], key='-RECOVERY_TAPE-', size=(25, 1), enable_events=True),
             sg.Button('Load Tape Contents', key='-LOAD_TAPE-')],
            [sg.Text('Archive:', size=(10, 1)),
             sg.Combo([], key='-RECOVERY_ARCHIVE-', size=(40, 1), enable_events=True)]
        ]
        
        # Recovery options
        recovery_options_frame = [
            [sg.Text('Recovery Mode:', font=('Arial', 10, 'bold'))],
            [sg.Radio('Complete Archive', 'RECOVERY_MODE', key='-RECOVER_ALL-', default=True),
             sg.Radio('Selected Files Only', 'RECOVERY_MODE', key='-RECOVER_SELECTED-')],
            [sg.Text('Output Directory:', size=(12, 1)),
             sg.Input(key='-RECOVERY_OUTPUT-', size=(40, 1)),
             sg.FolderBrowse()],
            [sg.Checkbox('Verify After Recovery', key='-VERIFY_RECOVERY-', default=True),
             sg.Checkbox('Preserve Directory Structure', key='-PRESERVE_STRUCTURE-', default=True)]
        ]
        
        # File list for selective recovery
        file_list_frame = [
            [sg.Text('Archive Contents:', font=('Arial', 10, 'bold'))],
            [sg.Table(
                values=[],
                headings=['File Path', 'Size', 'Modified', 'Type'],
                key='-RECOVERY_FILES-',
                auto_size_columns=False,
                col_widths=[50, 12, 15, 8],
                num_rows=15,
                alternating_row_color='lightgray',
                enable_events=True,
                select_mode=sg.TABLE_SELECT_MODE_EXTENDED
            )]
        ]
        
        # Recovery progress
        recovery_progress_frame = [
            [sg.Text('Recovery Progress:', font=('Arial', 10, 'bold'))],
            [sg.ProgressBar(100, key='-RECOVERY_PROGRESS-', size=(50, 20))],
            [sg.Text('Status:', size=(8, 1)), sg.Text('Ready', key='-RECOVERY_STATUS-', size=(60, 1))],
            [sg.Multiline(size=(100, 8), key='-RECOVERY_LOG-', disabled=True, autoscroll=True)]
        ]
        
        # Recovery controls
        recovery_controls_frame = [
            [sg.Button('Start Recovery', key='-START_RECOVERY-', size=(12, 1), disabled=True),
             sg.Button('Cancel Recovery', key='-CANCEL_RECOVERY-', size=(12, 1), disabled=True),
             sg.Button('Browse Archives', key='-BROWSE_ARCHIVES-', size=(12, 1))]
        ]
        
        return [
            [sg.Frame('Tape Selection', tape_select_frame, expand_x=True)],
            [sg.Frame('Recovery Options', recovery_options_frame, expand_x=True)],
            [sg.Frame('File Selection', file_list_frame, expand_x=True, expand_y=True)],
            [sg.Frame('Recovery Progress', recovery_progress_frame, expand_x=True)],
            [sg.Frame('Controls', recovery_controls_frame, expand_x=True)]
        ]
    
    def create_search_tab(self):
        """Create the search tab layout."""
        # Search input
        search_input_frame = [
            [sg.Text('Search Query:', size=(12, 1)),
             sg.Input(key='-SEARCH_QUERY-', size=(40, 1)),
             sg.Button('Search', key='-SEARCH_BTN-', bind_return_key=True),
             sg.Button('Advanced Search', key='-ADV_SEARCH_BTN-')],
            [sg.Text('File Type:', size=(12, 1)),
             sg.Combo(['All Types', '.txt', '.jpg', '.png', '.pdf', '.doc', '.zip', '.mp4'], 
                     default_value='All Types', key='-SEARCH_TYPE-', size=(15, 1)),
             sg.Text('Tape Filter:', size=(10, 1)),
             sg.Combo(['All Tapes'], key='-SEARCH_TAPE-', size=(20, 1))]
        ]
        
        # Search results
        search_results_frame = [
            [sg.Text('Search Results:', font=('Arial', 10, 'bold')),
             sg.Text('0 files found', key='-SEARCH_COUNT-', justification='right')],
            [sg.Table(
                values=[],
                headings=['File Path', 'Size', 'Modified', 'Archive', 'Tape'],
                key='-SEARCH_RESULTS-',
                auto_size_columns=False,
                col_widths=[40, 12, 15, 25, 15],
                num_rows=12,
                alternating_row_color='lightblue',
                enable_events=True,
                select_mode=sg.TABLE_SELECT_MODE_EXTENDED
            )]
        ]
        
        # File details
        file_details_frame = [
            [sg.Text('Selected File Details:', font=('Arial', 10, 'bold'))],
            [sg.Multiline(size=(100, 6), key='-SEARCH_DETAILS-', disabled=True)]
        ]
        
        # Search controls
        search_controls_frame = [
            [sg.Button('Recover Selected', key='-SEARCH_RECOVER-', size=(12, 1), disabled=True),
             sg.Button('Show in Archive', key='-SEARCH_SHOW_ARCHIVE-', size=(12, 1), disabled=True),
             sg.Button('Export Results', key='-SEARCH_EXPORT-', size=(12, 1)),
             sg.Button('Clear Results', key='-SEARCH_CLEAR-', size=(12, 1))]
        ]
        
        return [
            [sg.Frame('Search Input', search_input_frame, expand_x=True)],
            [sg.Frame('Search Results', search_results_frame, expand_x=True, expand_y=True)],
            [sg.Frame('File Details', file_details_frame, expand_x=True)],
            [sg.Frame('Actions', search_controls_frame, expand_x=True)]
        ]
    
    def create_management_tab(self):
        """Create the tape management tab layout."""
        # Tape library overview
        library_stats_frame = [
            [sg.Text('Tape Library Statistics:', font=('Arial', 10, 'bold'))],
            [sg.Text('Total Tapes:', size=(15, 1)), sg.Text('0', key='-STAT_TOTAL_TAPES-')],
            [sg.Text('Active Tapes:', size=(15, 1)), sg.Text('0', key='-STAT_ACTIVE_TAPES-')],
            [sg.Text('Total Archives:', size=(15, 1)), sg.Text('0', key='-STAT_TOTAL_ARCHIVES-')],
            [sg.Text('Total Files:', size=(15, 1)), sg.Text('0', key='-STAT_TOTAL_FILES-')],
            [sg.Text('Total Capacity:', size=(15, 1)), sg.Text('0 GB', key='-STAT_TOTAL_SIZE-')]
        ]
        
        # Tape list
        tape_list_frame = [
            [sg.Text('Tape Inventory:', font=('Arial', 10, 'bold')),
             sg.Push(),
             sg.Button('Refresh', key='-REFRESH_TAPES-'),
             sg.Button('Add Tape', key='-ADD_TAPE-')],
            [sg.Table(
                values=[],
                headings=['Label', 'Device', 'Status', 'Size', 'Archives', 'Created'],
                key='-TAPE_LIST-',
                auto_size_columns=False,
                col_widths=[15, 12, 10, 12, 10, 12],
                num_rows=12,
                alternating_row_color='lightgray',
                enable_events=True,
                select_mode=sg.TABLE_SELECT_MODE_BROWSE
            )]
        ]
        
        # Tape details
        tape_details_frame = [
            [sg.Text('Selected Tape Details:', font=('Arial', 10, 'bold'))],
            [sg.Text('Label:', size=(8, 1)), sg.Input(key='-TAPE_DETAIL_LABEL-', size=(20, 1), disabled=True)],
            [sg.Text('Status:', size=(8, 1)), 
             sg.Combo(['active', 'full', 'damaged', 'retired'], key='-TAPE_DETAIL_STATUS-', size=(12, 1), disabled=True)],
            [sg.Text('Notes:', size=(8, 1))],
            [sg.Multiline(key='-TAPE_DETAIL_NOTES-', size=(60, 4), disabled=True)]
        ]
        
        # Management controls
        manage_controls_frame = [
            [sg.Button('Edit Tape', key='-EDIT_TAPE-', size=(12, 1), disabled=True),
             sg.Button('Delete Tape', key='-DELETE_TAPE-', size=(12, 1), disabled=True),
             sg.Button('Browse Tape', key='-BROWSE_TAPE-', size=(12, 1), disabled=True)],
            [sg.Button('Export Inventory', key='-EXPORT_INVENTORY-', size=(12, 1)),
             sg.Button('Import Data', key='-IMPORT_DATA-', size=(12, 1)),
             sg.Button('Database Maintenance', key='-DB_MAINTENANCE-', size=(15, 1))]
        ]
        
        left_column = [
            [sg.Frame('Library Statistics', library_stats_frame)],
            [sg.Frame('Tape Details', tape_details_frame)],
            [sg.Frame('Management', manage_controls_frame)]
        ]
        
        right_column = [
            [sg.Frame('Tape Inventory', tape_list_frame, expand_x=True, expand_y=True)]
        ]
        
        return [
            [sg.Column(left_column, size=(400, 600)),
             sg.VSeperator(),
             sg.Column(right_column, expand_x=True, expand_y=True)]
        ]
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_dir = Path('../logs')
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'gui.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def initialize_managers(self):
        """Initialize the backend managers."""
        try:
            self.dep_manager = DependencyManager()
            if not self.dep_manager.detect_dependencies():
                sg.popup_error(
                    'Missing Dependencies',
                    'Required dependencies (tar, dd) not found.\n'
                    'Please install MSYS2 or add these tools to your PATH.',
                    title='Dependency Error'
                )
                exit(1)
            
            # Initialize core managers
            self.archive_manager = ArchiveManager(self.dep_manager)
            self.tape_manager = TapeManager(self.dep_manager)
            self.logger_manager = LoggerManager()
            
            # Initialize database and recovery components
            self.db_manager = DatabaseManager()
            self.recovery_manager = RecoveryManager(self.dep_manager, self.db_manager)
            
            # Initialize search and browser components
            self.search_interface = SearchInterface(self.db_manager, self.recovery_manager)
            self.advanced_search = AdvancedSearchManager(self.db_manager)
            self.tape_browser = TapeBrowser(self.db_manager, self.recovery_manager)
            
            # Initialize tape library management
            from tape_library import TapeLibrary
            self.tape_library = TapeLibrary(self.db_manager)
            
            # Integrate database with archive manager
            self.archive_manager.db_manager = self.db_manager
            
            self.logger.info("All managers initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize managers: {e}")
            sg.popup_error('Initialization Error', f'Failed to initialize: {e}')
            exit(1)
    
    def create_gui(self):
        """Create the main GUI window."""
        # Source folder selection
        folder_frame = [
            [sg.Text('Source Folder:', size=(12, 1)), 
             sg.Input(key='-FOLDER-', size=(50, 1)), 
             sg.FolderBrowse()],
            [sg.Text('Estimated Size:', size=(12, 1)), 
             sg.Text('Not calculated', key='-SIZE-', size=(30, 1))]
        ]
        
        # Tape device selection
        devices = self.tape_manager.detect_tape_devices()
        if not devices:
            devices = ['\\.\\Tape0']  # Default even if not detected
        
        device_frame = [
            [sg.Text('Tape Device:', size=(12, 1)), 
             sg.Combo(devices, default_value=devices[0], key='-DEVICE-', size=(20, 1)),
             sg.Button('Refresh Devices', key='-REFRESH-')],
            [sg.Text('Tape Status:', size=(12, 1)), 
             sg.Text('Unknown', key='-TAPE_STATUS-', size=(30, 1))]
        ]
        
        # Archive options
        options_frame = [
            [sg.Text('Archive Mode:', size=(12, 1)),
             sg.Radio('Stream to Tape', 'MODE', key='-STREAM-', default=True),
             sg.Radio('Cache & Write', 'MODE', key='-CACHED-')],
            [sg.Text('Copies:', size=(12, 1)),
             sg.Radio('1 Tape', 'COPIES', key='-COPY1-', default=True),
             sg.Radio('2 Tapes', 'COPIES', key='-COPY2-')],
            [sg.Checkbox('Compression', key='-COMPRESS-')]
        ]
        
        # Progress and logging
        progress_frame = [
            [sg.Text('Progress:'), sg.ProgressBar(100, key='-PROGRESS-', size=(40, 20))],
            [sg.Text('Status:', size=(8, 1)), sg.Text('Ready', key='-STATUS-', size=(50, 1))],
            [sg.Multiline(size=(80, 10), key='-LOG-', disabled=True, autoscroll=True)]
        ]
        
        # Control buttons
        button_frame = [
            [sg.Button('Start Archive', key='-START-', size=(12, 1)),
             sg.Button('Cancel', key='-CANCEL-', size=(12, 1), disabled=True),
             sg.Button('Exit', key='-EXIT-', size=(12, 1))]
        ]
        
        # Main layout
        layout = [
            [sg.Frame('Source Folder', folder_frame, expand_x=True)],
            [sg.Frame('Tape Device', device_frame, expand_x=True)],
            [sg.Frame('Archive Options', options_frame, expand_x=True)],
            [sg.Frame('Progress', progress_frame, expand_x=True)],
            [sg.Frame('Controls', button_frame, expand_x=True)]
        ]
        
        self.window = sg.Window(
            MAIN_WINDOW_TITLE,
            layout,
            resizable=True,
            finalize=True
        )
        
        # Initial status update
        self.update_tape_status()
    
    def update_tape_status(self):
        """Update the tape device status display."""
        try:
            device = self.window['-DEVICE-'].get()
            status = self.tape_manager.get_tape_status(device)
            status_text = f"{status['status']}: {status['details'][:30]}..."
            self.window['-TAPE_STATUS-'].update(status_text)
        except Exception as e:
            self.window['-TAPE_STATUS-'].update(f"Error: {str(e)[:30]}...")
    
    def update_folder_size(self, folder_path):
        """Update the estimated folder size display."""
        try:
            if folder_path and os.path.exists(folder_path):
                size, count = self.archive_manager.estimate_archive_size(folder_path)
                size_mb = size / (1024 * 1024)
                self.window['-SIZE-'].update(f"{size_mb:.1f} MB ({count} files)")
            else:
                self.window['-SIZE-'].update("Not calculated")
        except Exception as e:
            self.window['-SIZE-'].update(f"Error: {e}")
    
    def log_message(self, message):
        """Add a message to the log display."""
        timestamp = time.strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        self.window['-LOG-'].print(log_entry, end='')
    
    def update_progress(self, percent, status=""):
        """Update the progress bar and status."""
        self.window['-PROGRESS-'].update(percent)
        if status:
            self.window['-STATUS-'].update(status)
    
    def start_archive_job(self, config):
        """Start the archive job in a separate thread."""
        # Pre-flight checks and duplicate detection
        if not self.pre_archive_checks(config):
            self.window['-START-'].update(disabled=False)
            self.window['-CANCEL-'].update(disabled=True)
            return
        
        self.job_thread = threading.Thread(
            target=self.run_archive_job,
            args=(config,),
            daemon=True
        )
        self.job_thread.start()
    
    def run_archive_job(self, config):
        """Run the archive job (called in separate thread)."""
        try:
            self.log_message("Starting archive job...")
            
            folder_path = config['folder']
            device = config['device']
            mode = config['mode']
            copies = config['copies']
            compression = config['compression']
            
            # Progress callback
            def progress_callback(data):
                if isinstance(data, dict):
                    if 'percent' in data:
                        self.update_progress(data['percent'], data.get('status', ''))
                    else:
                        self.log_message(data.get('status', str(data)))
                else:
                    self.log_message(str(data))
            
            if mode == ArchiveMode.STREAM:
                # Stream mode
                self.log_message(f"Streaming {folder_path} to tape {device}")
                success = self.tape_manager.stream_to_tape(
                    folder_path, device, compression, progress_callback
                )
                
                if success:
                    self.log_message("Streaming completed successfully")
                    if copies == 2:
                        self.handle_second_copy(folder_path, device, compression, progress_callback)
                else:
                    self.log_message("Streaming failed")
                    
            else:
                # Cached mode
                self.log_message("Creating archive file...")
                archive_path, checksum = self.archive_manager.create_cached_archive(
                    folder_path, compression=compression, progress_callback=progress_callback
                )
                
                self.log_message(f"Archive created: {archive_path}")
                self.log_message(f"Checksum: {checksum[:16]}...")
                
                # Write to tape
                self.log_message(f"Writing archive to tape {device}")
                success, bytes_written = self.tape_manager.write_archive_to_tape(
                    archive_path, device, progress_callback
                )
                
                if success:
                    self.log_message(f"Archive written successfully ({bytes_written} bytes)")
                    if copies == 2:
                        self.handle_second_copy_cached(archive_path, device, progress_callback)
                else:
                    self.log_message("Archive write failed")
            
            self.update_progress(100, "Job completed")
            self.log_message("Archive job finished")
            
        except Exception as e:
            self.log_message(f"Error during archive job: {e}")
            self.logger.error(f"Archive job error: {e}")
        
        finally:
            # Re-enable start button
            self.window.write_event_value('-JOB_DONE-', None)
    
    def handle_second_copy(self, folder_path, device, compression, progress_callback):
        """Handle second tape copy for streaming mode."""
        result = sg.popup_yes_no(
            'Second Copy',
            'Insert second tape and click Yes to create second copy.',
            title='Second Tape Copy'
        )
        
        if result == 'Yes':
            self.log_message("Creating second copy...")
            self.tape_manager.rewind_tape(device)
            success = self.tape_manager.stream_to_tape(
                folder_path, device, compression, progress_callback
            )
            if success:
                self.log_message("Second copy completed successfully")
            else:
                self.log_message("Second copy failed")
    
    def handle_second_copy_cached(self, archive_path, device, progress_callback):
        """Handle second tape copy for cached mode."""
        result = sg.popup_yes_no(
            'Second Copy',
            'Insert second tape and click Yes to create second copy.',
            title='Second Tape Copy'
        )
        
        if result == 'Yes':
            self.log_message("Writing second copy...")
            self.tape_manager.rewind_tape(device)
            success, bytes_written = self.tape_manager.write_archive_to_tape(
                archive_path, device, progress_callback
            )
            if success:
                self.log_message(f"Second copy completed successfully ({bytes_written} bytes)")
            else:
                self.log_message("Second copy failed")
    
    def run(self):
        """Main GUI event loop with tabbed interface support."""
        self.update_log(INIT_MESSAGE)
        self.populate_recovery_tapes()
        self.populate_search_tapes()
        self.update_management_stats()
        
        while True:
            event, values = self.window.read(timeout=100)
            
            if event in (sg.WIN_CLOSED, '-EXIT-'):
                break
            
            # Archive Tab Events
            elif event == '-FOLDER-':
                folder_path = values['-FOLDER-']
                if folder_path:
                    threading.Thread(
                        target=self.update_folder_size,
                        args=(folder_path,),
                        daemon=True
                    ).start()
                    # Update suggested tape with duplicate check
                    self.update_suggested_tape_with_duplicates(folder_path)
            
            elif event == '-CALC_SIZE-':
                folder_path = values['-FOLDER-']
                if folder_path:
                    self.update_folder_size(folder_path)
            
            elif event == '-REFRESH-':
                devices = self.tape_manager.detect_tape_devices()
                if not devices:
                    devices = ['\\.\\Tape0']
                self.window['-DEVICE-'].update(values=devices, value=devices[0])
                self.update_tape_status()
            
            elif event == '-START-':
                self.handle_start_archive(values)
            
            elif event == '-CANCEL-':
                self.handle_cancel_archive()
            
            elif event == '-PREVIEW-':
                self.handle_preview_files(values['-FOLDER-'])
            
            # Recovery Tab Events
            elif event == '-RECOVERY_TAPE-':
                self.handle_recovery_tape_selection(values['-RECOVERY_TAPE-'])
            
            elif event == '-LOAD_TAPE-':
                self.handle_load_tape_contents(values['-RECOVERY_TAPE-'])
            
            elif event == '-RECOVERY_ARCHIVE-':
                self.handle_recovery_archive_selection(values['-RECOVERY_ARCHIVE-'])
            
            elif event == '-START_RECOVERY-':
                self.handle_start_recovery(values)
            
            elif event == '-CANCEL_RECOVERY-':
                self.handle_cancel_recovery()
            
            elif event == '-BROWSE_ARCHIVES-':
                self.handle_browse_archives()
            
            # Search Tab Events
            elif event == '-SEARCH_BTN-':
                self.handle_search(values)
            
            elif event == '-ADV_SEARCH_BTN-':
                self.handle_advanced_search()
            
            elif event == '-SEARCH_RESULTS-':
                self.handle_search_selection(values['-SEARCH_RESULTS-'])
            
            elif event == '-SEARCH_RECOVER-':
                self.handle_search_recover(values)
            
            elif event == '-SEARCH_SHOW_ARCHIVE-':
                self.handle_search_show_archive(values)
            
            elif event == '-SEARCH_EXPORT-':
                self.handle_search_export()
            
            elif event == '-SEARCH_CLEAR-':
                self.handle_search_clear()
            
            # Management Tab Events
            elif event == '-REFRESH_TAPES-':
                self.update_tape_list()
            
            elif event == '-ADD_TAPE-':
                self.handle_add_tape()
            
            elif event == '-TAPE_LIST-':
                self.handle_tape_selection(values['-TAPE_LIST-'])
            
            elif event == '-EDIT_TAPE-':
                self.handle_edit_tape(values)
            
            elif event == '-DELETE_TAPE-':
                self.handle_delete_tape(values)
            
            elif event == '-BROWSE_TAPE-':
                self.handle_browse_tape(values)
            
            elif event == '-EXPORT_INVENTORY-':
                self.handle_export_inventory()
            
            elif event == '-IMPORT_DATA-':
                self.handle_import_data()
            
            elif event == '-DB_MAINTENANCE-':
                self.handle_db_maintenance()
            
            elif event == '-JOB_DONE-':
                # Archive job finished, re-enable controls
                self.window['-START-'].update(disabled=False)
                self.window['-CANCEL-'].update(disabled=True)
            
            elif event == '-RECOVERY_DONE-':
                # Recovery job finished, re-enable controls
                self.window['-START_RECOVERY-'].update(disabled=False)
                self.window['-CANCEL_RECOVERY-'].update(disabled=True)
                self.window['-RECOVERY_PROGRESS-'].update(100)
                self.window['-RECOVERY_STATUS-'].update("Recovery completed")
        
        # Cleanup
        if self.archive_manager:
            self.archive_manager.cleanup()
        
        self.window.close()
    
    def pre_archive_checks(self, config):
        """Perform pre-archive checks including duplicate detection and tape suggestions."""
        try:
            folder_path = config['folder']
            
            # Check for existing archives of this folder
            if self.db_manager:
                existing_archives = self.archive_manager.find_archives_by_folder(folder_path)
                if existing_archives:
                    archive_list = "\n".join([
                        f"• {arch['archive_name']} on {arch['tape_label']} ({arch['archive_date'][:10]})"
                        for arch in existing_archives[:5]
                    ])
                    
                    if len(existing_archives) > 5:
                        archive_list += f"\n... and {len(existing_archives) - 5} more"
                    
                    result = sg.popup_yes_no(
                        f"Duplicate Archive Warning\n\n"
                        f"Found {len(existing_archives)} existing archive(s) for this folder:\n\n"
                        f"{archive_list}\n\n"
                        f"Do you want to continue with creating a new archive?",
                        title="Duplicate Archive Detected"
                    )
                    
                    if result != 'Yes':
                        return False
                
                # Show suggested tape if indexing enabled
                if config['index_files']:
                    estimated_size, _ = self.archive_manager.estimate_archive_size(folder_path)
                    suggested_tape = self.archive_manager.suggest_tape_for_new_archive(estimated_size)
                    
                    if suggested_tape:
                        current_device = config['device']
                        suggested_device = suggested_tape['tape_device']
                        
                        if current_device != suggested_device:
                            result = sg.popup_yes_no(
                                f"Tape Optimization Suggestion\n\n"
                                f"Current device: {current_device}\n"
                                f"Suggested tape: {suggested_tape['tape_label']} on {suggested_device}\n"
                                f"Remaining space: {suggested_tape['remaining_space']/1024/1024/1024:.1f} GB\n\n"
                                f"Would you like to switch to the suggested tape?",
                                title="Tape Suggestion"
                            )
                            
                            if result == 'Yes':
                                # Update the device in the config
                                config['device'] = suggested_device
                                self.window['-DEVICE-'].update(suggested_device)
                                self.update_log(f"Switched to suggested tape: {suggested_tape['tape_label']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pre-archive check failed: {e}")
            sg.popup_error('Pre-flight Check Error', f'Failed to perform pre-archive checks: {e}')
            return False
    
    def generate_tape_label(self, device):
        """Generate a tape label based on device and current date."""
        try:
            # Try to get existing tape label from database
            if self.db_manager:
                existing_tapes = self.db_manager.get_tapes_by_device(device)
                if existing_tapes:
                    return existing_tapes[0]['tape_label']
            
            # Generate new label
            date_str = time.strftime('%Y%m%d')
            return f"LTO_{date_str}_{device.replace('\\', '').replace('.', '').replace('Tape', 'T')}"
            
        except Exception as e:
            self.logger.warning(f"Failed to generate tape label: {e}")
            return f"LTO_TAPE_{int(time.time())}"
    
    def update_log(self, message, tab='archive'):
        """Add a message to the appropriate log display."""
        timestamp = time.strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        if tab == 'archive':
            self.window['-LOG-'].print(log_entry, end='')
        elif tab == 'recovery':
            self.window['-RECOVERY_LOG-'].print(log_entry, end='')
    
    def update_suggested_tape_with_duplicates(self, folder_path):
        """Update suggested tape based on folder size with duplicate detection."""
        try:
            if folder_path and os.path.exists(folder_path):
                # Check for duplicates first
                existing_archives = self.archive_manager.find_archives_by_folder(folder_path)
                
                if existing_archives:
                    latest_archive = existing_archives[0]
                    suggestion_text = f"⚠️ Duplicate found: {latest_archive['tape_label']} ({latest_archive['archive_date'][:10]})"
                    self.window['-SUGGESTED_TAPE-'].update(suggestion_text)
                else:
                    # No duplicates, suggest optimal tape
                    size, _ = self.archive_manager.estimate_archive_size(folder_path)
                    suggested = self.tape_library.suggest_best_tape(size)
                    
                    if suggested:
                        remaining_gb = suggested['remaining_space'] / (1024**3)
                        suggestion_text = f"✓ {suggested['tape_label']} ({remaining_gb:.1f} GB available)"
                        self.window['-SUGGESTED_TAPE-'].update(suggestion_text)
                    else:
                        self.window['-SUGGESTED_TAPE-'].update("No suitable tape found - may need new tape")
        except Exception as e:
            self.window['-SUGGESTED_TAPE-'].update(f"Error: {e}")
    
    def update_suggested_tape(self, folder_path):
        """Legacy method - redirects to enhanced version."""
        self.update_suggested_tape_with_duplicates(folder_path)
    
    def populate_recovery_tapes(self):
        """Populate recovery tape dropdown."""
        try:
            tapes = self.db_manager.get_all_tapes()
            tape_options = [f"{tape['tape_label']} ({tape['tape_device']})" for tape in tapes]
            self.window['-RECOVERY_TAPE-'].update(values=tape_options)
        except Exception as e:
            self.logger.error(f"Failed to populate recovery tapes: {e}")
    
    def populate_search_tapes(self):
        """Populate search tape filter dropdown."""
        try:
            tapes = self.db_manager.get_all_tapes()
            tape_options = ['All Tapes'] + [tape['tape_label'] for tape in tapes]
            self.window['-SEARCH_TAPE-'].update(values=tape_options, value='All Tapes')
        except Exception as e:
            self.logger.error(f"Failed to populate search tapes: {e}")
    
    def update_management_stats(self):
        """Update management tab statistics."""
        try:
            stats = self.db_manager.get_library_statistics()
            self.window['-STAT_TOTAL_TAPES-'].update(str(stats.get('total_tapes', 0)))
            self.window['-STAT_ACTIVE_TAPES-'].update(str(stats.get('active_tapes', 0)))
            self.window['-STAT_TOTAL_ARCHIVES-'].update(str(stats.get('total_archives', 0)))
            self.window['-STAT_TOTAL_FILES-'].update(f"{stats.get('total_files', 0):,}")
            self.window['-STAT_TOTAL_SIZE-'].update(f"{stats.get('total_size_gb', 0):.1f} GB")
        except Exception as e:
            self.logger.error(f"Failed to update statistics: {e}")
    
    def handle_start_archive(self, values):
        """Handle start archive button click."""
        folder_path = values['-FOLDER-']
        if not folder_path:
            sg.popup_error('Error', 'Please select a source folder')
            return
        
        valid, message = self.archive_manager.validate_source_folder(folder_path)
        if not valid:
            sg.popup_error('Folder Error', message)
            return
        
        # Build job configuration
        config = {
            'folder': folder_path,
            'device': values['-DEVICE-'],
            'mode': 'stream' if values['-STREAM-'] else 'cached',
            'copies': 2 if values['-COPY2-'] else 1,
            'compression': values['-COMPRESS-'],
            'index_files': values['-INDEX_FILES-'],
            'archive_name': values['-ARCHIVE_NAME-'].strip() or None
        }
        
        # Disable start button and enable cancel
        self.window['-START-'].update(disabled=True)
        self.window['-CANCEL-'].update(disabled=False)
        
        # Start the job
        self.start_archive_job(config)
    
    def handle_cancel_archive(self):
        """Handle cancel archive button click."""
        self.update_log("Cancel requested - job will stop after current operation")
        # TODO: Implement proper cancellation
    
    def handle_preview_files(self, folder_path):
        """Handle preview files button click."""
        if not folder_path:
            sg.popup_error('Error', 'Please select a source folder')
            return
        
        try:
            files = self.archive_manager.get_file_list(folder_path)
            preview_text = f"Files to be archived ({len(files)} total):\n\n"
            for file_path in files[:100]:  # Show first 100 files
                preview_text += f"{file_path}\n"
            
            if len(files) > 100:
                preview_text += f"\n... and {len(files) - 100} more files"
            
            sg.popup_scrolled(preview_text, title='File Preview', size=(80, 30))
        except Exception as e:
            sg.popup_error('Preview Error', f'Failed to preview files: {e}')
    
    def handle_recovery_tape_selection(self, tape_selection):
        """Handle recovery tape selection."""
        if not tape_selection:
            return
        
        try:
            tape_label = tape_selection.split(' (')[0]
            tape = self.db_manager.find_tape_by_label(tape_label)
            if tape:
                archives = self.db_manager.get_tape_contents(tape['tape_id'])
                archive_options = [archive['archive_name'] for archive in archives]
                self.window['-RECOVERY_ARCHIVE-'].update(values=archive_options)
        except Exception as e:
            self.logger.error(f"Failed to load tape archives: {e}")
    
    def handle_search(self, values):
        """Handle search button click."""
        query = values['-SEARCH_QUERY-'].strip()
        if not query:
            sg.popup('Please enter a search query')
            return
        
        try:
            filters = {
                'file_type': values['-SEARCH_TYPE-'] if values['-SEARCH_TYPE-'] != 'All Types' else None,
                'tape_label': values['-SEARCH_TAPE-'] if values['-SEARCH_TAPE-'] != 'All Tapes' else None
            }
            
            results = self.search_interface.search_files(query, filters)
            self.search_interface.display_search_results(results)
            
            # Update count
            self.window['-SEARCH_COUNT-'].update(f'{len(results)} files found')
            
        except Exception as e:
            sg.popup_error('Search Error', f'Search failed: {e}')
    
    def handle_advanced_search(self):
        """Handle advanced search button click."""
        try:
            adv_gui = AdvancedSearchGUI(self.db_manager, self.advanced_search)
            adv_gui.run_advanced_search_interface()
        except Exception as e:
            sg.popup_error('Advanced Search Error', f'Failed to open advanced search: {e}')
    
    def handle_browse_archives(self):
        """Handle browse archives button click."""
        try:
            self.tape_browser.run_browser_interface()
        except Exception as e:
            sg.popup_error('Browser Error', f'Failed to open tape browser: {e}')
    
    def update_tape_list(self):
        """Update the tape list in management tab."""
        try:
            tapes = self.db_manager.get_all_tapes()
            table_data = []
            
            for tape in tapes:
                archives = self.db_manager.get_tape_contents(tape['tape_id'])
                size_gb = (tape.get('total_size_bytes', 0) or 0) / (1024**3)
                
                table_data.append([
                    tape['tape_label'],
                    tape.get('tape_device', 'Unknown'),
                    tape.get('tape_status', 'unknown'),
                    f"{size_gb:.1f} GB",
                    str(len(archives)),
                    tape.get('created_date', 'Unknown')[:10] if tape.get('created_date') else 'Unknown'
                ])
            
            self.window['-TAPE_LIST-'].update(values=table_data)
            self.update_management_stats()
            
        except Exception as e:
            self.logger.error(f"Failed to update tape list: {e}")
    
    def handle_add_tape(self):
        """Handle add tape button click."""
        layout = [
            [sg.Text('Add New Tape to Library')],
            [sg.Text('Tape Label:', size=(12, 1)), sg.Input(key='-NEW_TAPE_LABEL-', size=(20, 1))],
            [sg.Text('Device:', size=(12, 1)), sg.Input(key='-NEW_TAPE_DEVICE-', size=(20, 1))],
            [sg.Text('Notes:', size=(12, 1))],
            [sg.Multiline(key='-NEW_TAPE_NOTES-', size=(40, 3))],
            [sg.Button('Add Tape', key='-ADD_NEW_TAPE-'), sg.Button('Cancel', key='-CANCEL_ADD-')]
        ]
        
        add_window = sg.Window('Add Tape', layout, modal=True)
        
        while True:
            event, values = add_window.read()
            
            if event in (sg.WIN_CLOSED, '-CANCEL_ADD-'):
                break
            elif event == '-ADD_NEW_TAPE-':
                try:
                    tape_id = self.db_manager.add_tape(
                        tape_label=values['-NEW_TAPE_LABEL-'],
                        device=values['-NEW_TAPE_DEVICE-'],
                        notes=values['-NEW_TAPE_NOTES-']
                    )
                    sg.popup(f'Tape added successfully with ID: {tape_id}')
                    self.update_tape_list()
                    self.populate_recovery_tapes()
                    self.populate_search_tapes()
                    break
                except Exception as e:
                    sg.popup_error('Add Tape Error', f'Failed to add tape: {e}')
        
        add_window.close()
    
    def handle_db_maintenance(self):
        """Handle database maintenance button click."""
        try:
            from database_init import DatabaseInitializer
            
            db_init = DatabaseInitializer()
            
            layout = [
                [sg.Text('Database Maintenance', font=('Arial', 12, 'bold'))],
                [sg.HSeparator()],
                [sg.Button('Check Integrity', key='-CHECK_INTEGRITY-'),
                 sg.Button('Optimize Database', key='-OPTIMIZE_DB-')],
                [sg.Button('Backup Database', key='-BACKUP_DB-'),
                 sg.Button('Cleanup Temp Files', key='-CLEANUP_DB-')],
                [sg.HSeparator()],
                [sg.Multiline(size=(60, 10), key='-MAINTENANCE_LOG-', disabled=True)],
                [sg.Button('Close', key='-CLOSE_MAINTENANCE-')]
            ]
            
            maint_window = sg.Window('Database Maintenance', layout, modal=True)
            
            while True:
                event, values = maint_window.read()
                
                if event in (sg.WIN_CLOSED, '-CLOSE_MAINTENANCE-'):
                    break
                elif event == '-CHECK_INTEGRITY-':
                    result = db_init.check_database_integrity()
                    maint_window['-MAINTENANCE_LOG-'].print(f"Integrity check: {result}\n")
                elif event == '-OPTIMIZE_DB-':
                    db_init.optimize_database()
                    maint_window['-MAINTENANCE_LOG-'].print("Database optimized\n")
                elif event == '-BACKUP_DB-':
                    backup_path = db_init.backup_database()
                    maint_window['-MAINTENANCE_LOG-'].print(f"Database backed up to: {backup_path}\n")
                elif event == '-CLEANUP_DB-':
                    db_init.cleanup_temp_files()
                    maint_window['-MAINTENANCE_LOG-'].print("Temporary files cleaned up\n")
            
            maint_window.close()
            
        except Exception as e:
            sg.popup_error('Maintenance Error', f'Database maintenance failed: {e}')
    
    def handle_load_tape_contents(self, tape_selection):
        """Handle load tape contents button click."""
        if not tape_selection:
            sg.popup('Please select a tape first')
            return
        
        try:
            tape_label = tape_selection.split(' (')[0]
            tape = self.db_manager.find_tape_by_label(tape_label)
            if tape:
                archives = self.db_manager.get_tape_contents(tape['tape_id'])
                archive_options = [archive['archive_name'] for archive in archives]
                self.window['-RECOVERY_ARCHIVE-'].update(values=archive_options)
                self.window['-START_RECOVERY-'].update(disabled=False)
                self.update_log(f"Loaded {len(archives)} archives from tape {tape_label}", 'recovery')
        except Exception as e:
            sg.popup_error('Load Error', f'Failed to load tape contents: {e}')
    
    def handle_recovery_archive_selection(self, archive_selection):
        """Handle recovery archive selection."""
        if not archive_selection:
            return
        
        try:
            archive = self.db_manager.find_archive_by_name(archive_selection)
            if archive:
                files = self.db_manager.get_archive_files(archive['archive_id'])
                
                # Format files for table display
                table_data = []
                for file_info in files:
                    size_mb = (file_info.get('file_size_bytes', 0) or 0) / (1024*1024)
                    table_data.append([
                        file_info['file_path'],
                        f"{size_mb:.2f} MB",
                        file_info.get('file_modified', 'Unknown')[:16] if file_info.get('file_modified') else 'Unknown',
                        file_info.get('file_type', 'Unknown')
                    ])
                
                self.window['-RECOVERY_FILES-'].update(values=table_data)
                self.update_log(f"Loaded {len(files)} files from archive {archive_selection}", 'recovery')
        except Exception as e:
            sg.popup_error('Archive Error', f'Failed to load archive files: {e}')
    
    def handle_start_recovery(self, values):
        """Handle start recovery button click."""
        tape_selection = values['-RECOVERY_TAPE-']
        archive_selection = values['-RECOVERY_ARCHIVE-']
        output_dir = values['-RECOVERY_OUTPUT-']
        
        if not all([tape_selection, archive_selection, output_dir]):
            sg.popup_error('Recovery Error', 'Please select tape, archive, and output directory')
            return
        
        try:
            # Disable controls
            self.window['-START_RECOVERY-'].update(disabled=True)
            self.window['-CANCEL_RECOVERY-'].update(disabled=False)
            
            # Get recovery mode
            recover_all = values['-RECOVER_ALL-']
            selected_files = None
            
            if not recover_all:
                # Get selected files from table
                selected_rows = values['-RECOVERY_FILES-']
                if not selected_rows:
                    sg.popup('Please select files to recover or choose "Complete Archive" mode')
                    self.window['-START_RECOVERY-'].update(disabled=False)
                    self.window['-CANCEL_RECOVERY-'].update(disabled=True)
                    return
                
                # Extract file paths from selected rows
                table_data = self.window['-RECOVERY_FILES-'].get()
                selected_files = [table_data[row][0] for row in selected_rows]
            
            # Start recovery in separate thread
            def recovery_job():
                try:
                    tape_label = tape_selection.split(' (')[0]
                    tape = self.db_manager.find_tape_by_label(tape_label)
                    
                    def progress_callback(data):
                        if isinstance(data, dict):
                            if 'percent' in data:
                                self.window['-RECOVERY_PROGRESS-'].update(data['percent'])
                                self.window['-RECOVERY_STATUS-'].update(data.get('status', ''))
                            else:
                                self.update_log(data.get('status', str(data)), 'recovery')
                        else:
                            self.update_log(str(data), 'recovery')
                    
                    if recover_all:
                        result = self.recovery_manager.extract_archive(
                            tape['tape_device'], archive_selection, output_dir, progress_callback
                        )
                    else:
                        result = self.recovery_manager.extract_specific_files(
                            tape['tape_device'], archive_selection, selected_files, output_dir, progress_callback
                        )
                    
                    if result:
                        self.update_log("Recovery completed successfully", 'recovery')
                        
                        # Verify if requested
                        if values['-VERIFY_RECOVERY-']:
                            self.update_log("Verifying recovered files...", 'recovery')
                            archive = self.db_manager.find_archive_by_name(archive_selection)
                            verification_result = self.recovery_manager.verify_recovered_files(
                                output_dir, archive['archive_id']
                            )
                            if verification_result:
                                self.update_log("File verification passed", 'recovery')
                            else:
                                self.update_log("File verification failed - some files may be corrupted", 'recovery')
                    else:
                        self.update_log("Recovery failed", 'recovery')
                    
                except Exception as e:
                    self.update_log(f"Recovery error: {e}", 'recovery')
                
                finally:
                    # Re-enable controls
                    self.window.write_event_value('-RECOVERY_DONE-', None)
            
            threading.Thread(target=recovery_job, daemon=True).start()
            
        except Exception as e:
            sg.popup_error('Recovery Error', f'Failed to start recovery: {e}')
            self.window['-START_RECOVERY-'].update(disabled=False)
            self.window['-CANCEL_RECOVERY-'].update(disabled=True)
    
    def handle_cancel_recovery(self):
        """Handle cancel recovery button click."""
        self.update_log("Recovery cancellation requested", 'recovery')
        # TODO: Implement proper cancellation mechanism
    
    def handle_search_selection(self, selection):
        """Handle search results selection."""
        try:
            if selection:
                table_data = self.window['-SEARCH_RESULTS-'].get()
                if selection and len(table_data) > selection[0]:
                    selected_file = table_data[selection[0]]
                    
                    # Get file details
                    file_path = selected_file[0]
                    archive_name = selected_file[3]
                    tape_label = selected_file[4]
                    
                    details = f"File: {file_path}\n"
                    details += f"Size: {selected_file[1]}\n"
                    details += f"Modified: {selected_file[2]}\n"
                    details += f"Archive: {archive_name}\n"
                    details += f"Tape: {tape_label}\n"
                    
                    self.window['-SEARCH_DETAILS-'].update(details)
                    self.window['-SEARCH_RECOVER-'].update(disabled=False)
                    self.window['-SEARCH_SHOW_ARCHIVE-'].update(disabled=False)
        except Exception as e:
            self.logger.error(f"Search selection error: {e}")
    
    def handle_search_recover(self, values):
        """Handle recover selected files from search."""
        try:
            selected_rows = values['-SEARCH_RESULTS-']
            if not selected_rows:
                sg.popup('Please select files to recover')
                return
            
            output_dir = sg.popup_get_folder('Select recovery output directory')
            if not output_dir:
                return
            
            table_data = self.window['-SEARCH_RESULTS-'].get()
            
            for row in selected_rows:
                file_info = table_data[row]
                file_path = file_info[0]
                archive_name = file_info[3]
                tape_label = file_info[4]
                
                # Find tape and start recovery
                tape = self.db_manager.find_tape_by_label(tape_label)
                if tape:
                    result = self.recovery_manager.extract_specific_files(
                        tape['tape_device'], archive_name, [file_path], output_dir
                    )
                    if result:
                        sg.popup(f'Successfully recovered: {file_path}')
                    else:
                        sg.popup_error(f'Failed to recover: {file_path}')
        except Exception as e:
            sg.popup_error('Recovery Error', f'Search recovery failed: {e}')
    
    def handle_search_show_archive(self, values):
        """Handle show selected file in archive browser."""
        try:
            selected_rows = values['-SEARCH_RESULTS-']
            if not selected_rows:
                sg.popup('Please select a file first')
                return
            
            table_data = self.window['-SEARCH_RESULTS-'].get()
            file_info = table_data[selected_rows[0]]
            archive_name = file_info[3]
            
            # Open tape browser and navigate to archive
            self.tape_browser.run_browser_interface(archive_name)
        except Exception as e:
            sg.popup_error('Browser Error', f'Failed to show archive: {e}')
    
    def handle_search_export(self):
        """Handle export search results."""
        try:
            table_data = self.window['-SEARCH_RESULTS-'].get()
            if not table_data:
                sg.popup('No search results to export')
                return
            
            export_path = sg.popup_get_file(
                'Save search results',
                save_as=True,
                file_types=[('CSV Files', '*.csv')],
                default_extension='.csv'
            )
            
            if export_path:
                self.search_interface.export_search_results(table_data, export_path)
                sg.popup(f'Search results exported to: {export_path}')
        except Exception as e:
            sg.popup_error('Export Error', f'Failed to export results: {e}')
    
    def handle_search_clear(self):
        """Handle clear search results."""
        self.window['-SEARCH_RESULTS-'].update(values=[])
        self.window['-SEARCH_DETAILS-'].update('')
        self.window['-SEARCH_COUNT-'].update('0 files found')
        self.window['-SEARCH_RECOVER-'].update(disabled=True)
        self.window['-SEARCH_SHOW_ARCHIVE-'].update(disabled=True)
    
    def handle_tape_selection(self, selection):
        """Handle tape selection in management tab."""
        try:
            if selection:
                table_data = self.window['-TAPE_LIST-'].get()
                if selection and len(table_data) > selection[0]:
                    selected_tape = table_data[selection[0]]
                    tape_label = selected_tape[0]
                    
                    # Get tape details from database
                    tape = self.db_manager.find_tape_by_label(tape_label)
                    if tape:
                        self.window['-TAPE_DETAIL_LABEL-'].update(tape['tape_label'], disabled=False)
                        self.window['-TAPE_DETAIL_STATUS-'].update(tape.get('tape_status', 'unknown'), disabled=False)
                        self.window['-TAPE_DETAIL_NOTES-'].update(tape.get('notes', ''), disabled=False)
                        
                        # Enable management buttons
                        self.window['-EDIT_TAPE-'].update(disabled=False)
                        self.window['-DELETE_TAPE-'].update(disabled=False)
                        self.window['-BROWSE_TAPE-'].update(disabled=False)
        except Exception as e:
            self.logger.error(f"Tape selection error: {e}")
    
    def handle_edit_tape(self, values):
        """Handle edit tape button click."""
        try:
            selected_rows = values['-TAPE_LIST-']
            if not selected_rows:
                sg.popup('Please select a tape to edit')
                return
            
            table_data = self.window['-TAPE_LIST-'].get()
            tape_label = table_data[selected_rows[0]][0]
            tape = self.db_manager.find_tape_by_label(tape_label)
            
            if tape:
                # Update tape in database
                new_label = values['-TAPE_DETAIL_LABEL-']
                new_status = values['-TAPE_DETAIL_STATUS-']
                new_notes = values['-TAPE_DETAIL_NOTES-']
                
                self.db_manager.update_tape(
                    tape['tape_id'],
                    tape_label=new_label,
                    tape_status=new_status,
                    notes=new_notes
                )
                
                sg.popup('Tape updated successfully')
                self.update_tape_list()
                self.populate_recovery_tapes()
                self.populate_search_tapes()
        except Exception as e:
            sg.popup_error('Edit Error', f'Failed to edit tape: {e}')
    
    def handle_delete_tape(self, values):
        """Handle delete tape button click."""
        try:
            selected_rows = values['-TAPE_LIST-']
            if not selected_rows:
                sg.popup('Please select a tape to delete')
                return
            
            table_data = self.window['-TAPE_LIST-'].get()
            tape_label = table_data[selected_rows[0]][0]
            
            # Confirm deletion
            result = sg.popup_yes_no(
                f'Are you sure you want to delete tape "{tape_label}"?\n'
                'This will remove all associated archive and file records.',
                title='Confirm Deletion'
            )
            
            if result == 'Yes':
                tape = self.db_manager.find_tape_by_label(tape_label)
                if tape:
                    self.db_manager.delete_tape(tape['tape_id'])
                    sg.popup('Tape deleted successfully')
                    self.update_tape_list()
                    self.populate_recovery_tapes()
                    self.populate_search_tapes()
                    
                    # Clear details
                    self.window['-TAPE_DETAIL_LABEL-'].update('', disabled=True)
                    self.window['-TAPE_DETAIL_STATUS-'].update('', disabled=True)
                    self.window['-TAPE_DETAIL_NOTES-'].update('', disabled=True)
                    
                    # Disable buttons
                    self.window['-EDIT_TAPE-'].update(disabled=True)
                    self.window['-DELETE_TAPE-'].update(disabled=True)
                    self.window['-BROWSE_TAPE-'].update(disabled=True)
        except Exception as e:
            sg.popup_error('Delete Error', f'Failed to delete tape: {e}')
    
    def handle_browse_tape(self, values):
        """Handle browse tape button click."""
        try:
            selected_rows = values['-TAPE_LIST-']
            if not selected_rows:
                sg.popup('Please select a tape to browse')
                return
            
            table_data = self.window['-TAPE_LIST-'].get()
            tape_label = table_data[selected_rows[0]][0]
            
            # Open tape browser for specific tape
            self.tape_browser.run_browser_interface(tape_filter=tape_label)
        except Exception as e:
            sg.popup_error('Browse Error', f'Failed to browse tape: {e}')
    
    def handle_export_inventory(self):
        """Handle export inventory button click."""
        try:
            export_path = sg.popup_get_file(
                'Export Tape Inventory',
                save_as=True,
                file_types=[('CSV Files', '*.csv'), ('JSON Files', '*.json')],
                default_extension='.csv'
            )
            
            if export_path:
                if export_path.lower().endswith('.json'):
                    self.db_manager.export_inventory_json(export_path)
                else:
                    self.db_manager.export_inventory_csv(export_path)
                
                sg.popup(f'Inventory exported to: {export_path}')
        except Exception as e:
            sg.popup_error('Export Error', f'Failed to export inventory: {e}')
    
    def handle_import_data(self):
        """Handle import data button click."""
        try:
            import_path = sg.popup_get_file(
                'Import Data',
                file_types=[('CSV Files', '*.csv'), ('JSON Files', '*.json')]
            )
            
            if import_path:
                result = sg.popup_yes_no(
                    f'Import data from {import_path}?\n'
                    'This may overwrite existing data.',
                    title='Confirm Import'
                )
                
                if result == 'Yes':
                    if import_path.lower().endswith('.json'):
                        records_imported = self.db_manager.import_inventory_json(import_path)
                    else:
                        records_imported = self.db_manager.import_inventory_csv(import_path)
                    
                    sg.popup(f'Successfully imported {records_imported} records')
                    self.update_tape_list()
                    self.populate_recovery_tapes()
                    self.populate_search_tapes()
        except Exception as e:
            sg.popup_error('Import Error', f'Failed to import data: {e}')


def main():
    """Main entry point."""
    try:
        app = LTOArchiveGUI()
        app.run()
    except Exception as e:
        sg.popup_error('Fatal Error', f'Application failed to start: {e}')
        logging.error(f"Fatal error: {e}")


if __name__ == '__main__':
    main()

