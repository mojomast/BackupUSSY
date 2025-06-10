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
from archive_manager import ArchiveManager, ArchiveMode
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
            [sg.Frame('Device & Options', device_frame, expand_x=True)],
            [sg.Frame('Progress', progress_frame, expand_x=True)],
            [sg.Frame('Controls', button_frame, expand_x=True)]
        ]
        
        self.window = sg.Window(
            MAIN_WINDOW_TITLE,
            layout,
            resizable=True,
            finalize=True
        )
        
        # Initialize device list
        self.refresh_devices()
    
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
            daemon=True  # Add daemon=True so thread exits when main app exits
        )
        self.job_thread.start()
        self.current_job = self.job_thread # Or a more specific job object if available
        # Update UI
        self.window['-START-'].update(disabled=True)
        self.window['-CANCEL-'].update(disabled=False)
        self.window['-FOLDER-'].update(disabled=True) 
        self.window['-DEVICE-'].update(disabled=True)
        # Potentially disable other config options here
        self.log_message(f"Archive job started for: {config.get('archive_name', 'Unnamed Archive')}")
    
    def pre_archive_checks(self, config):
        """Perform pre-flight checks before starting archive."""
        folder_path = config.get('folder_path')
        device = config.get('device')
        
        # Check if folder exists
        if not folder_path or not os.path.exists(folder_path):
            sg.popup_error('Error', 'Source folder does not exist or is not selected')
            return False
        
        # Check if device is selected
        if not device:
            sg.popup_error('Error', 'Please select a tape device')
            return False
        
        # Validate folder is not empty
        try:
            if not any(os.listdir(folder_path)):
                sg.popup_error('Error', 'Source folder is empty')
                return False
        except PermissionError:
            sg.popup_error('Error', 'Permission denied accessing source folder')
            return False
        
        return True
    
    def update_log(self, message, log_type='main'):
        """Update the appropriate log display."""
        timestamp = time.strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        if log_type == 'recovery' and '-RECOVERY_LOG-' in self.window.AllKeysDict:
            self.window['-RECOVERY_LOG-'].print(log_entry, end='')
        elif '-LOG-' in self.window.AllKeysDict:
            self.window['-LOG-'].print(log_entry, end='')
    
    def create_main_layout(self):
        """Create the main GUI layout."""
        # Folder selection
        folder_frame = [
            [sg.Text('Select folder to archive:')],
            [sg.Input(key='-FOLDER-', size=(70, 1)), sg.FolderBrowse()],
            [sg.Text('Archive name (optional):')],
            [sg.Input(key='-ARCHIVE_NAME-', size=(70, 1))]
        ]
        
        # Device and options
        device_frame = [
            [sg.Text('Tape device:'), sg.Combo([], key='-DEVICE-', size=(30, 1), readonly=True),
             sg.Button('Refresh Devices', key='-REFRESH_DEVICES-')],
            [sg.Text('Archive mode:'), sg.Combo(['Stream', 'Cached'], key='-MODE-', default_value='Cached', readonly=True)],
            [sg.Text('Number of copies:'), sg.Combo([1, 2], key='-COPIES-', default_value=1, readonly=True)],
            [sg.Checkbox('Enable compression (gzip)', key='-COMPRESSION-', default=True),
             sg.Checkbox('Index files in database', key='-INDEX_FILES-', default=True)]
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
            [sg.Frame('Device & Options', device_frame, expand_x=True)],
            [sg.Frame('Progress', progress_frame, expand_x=True)],
            [sg.Frame('Controls', button_frame, expand_x=True)]
        ]
        
        self.window = sg.Window(
            MAIN_WINDOW_TITLE,
            layout,
            resizable=True,
            finalize=True
        )
        
        # Initialize device list
        self.refresh_devices()
    
    def refresh_devices(self):
        """Refresh the list of available tape devices."""
        try:
            devices = self.tape_manager.detect_tape_devices()
            self.window['-DEVICE-'].update(values=devices)
            if devices:
                self.window['-DEVICE-'].update(value=devices[0])
        except Exception as e:
            logger.error(f"Failed to refresh devices: {e}")
    
    def update_folder_size(self, folder_path):
        """Update the estimated folder size display."""
        try:
            if folder_path and os.path.exists(folder_path):
                size, count = self.archive_manager.estimate_archive_size(folder_path)
                size_mb = size / (1024 * 1024)
                logger.info(f"Folder size: {size_mb:.1f} MB ({count} files)")
        except Exception as e:
            logger.error(f"Failed to calculate folder size: {e}")
    
    def log_message(self, message):
        """Add a message to the log display."""
        timestamp = time.strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        if self.window and '-LOG-' in self.window.AllKeysDict:
            self.window['-LOG-'].print(log_entry, end='')
        logger.info(message)
    
    def update_progress(self, percent, status=""):
        """Update the progress bar and status."""
        if self.window:
            if '-PROGRESS-' in self.window.AllKeysDict:
                self.window['-PROGRESS-'].update(percent)
            if status and '-STATUS-' in self.window.AllKeysDict:
                self.window['-STATUS-'].update(status)
    
    def start_archive_job(self, config):
        """Start the archive job in a separate thread."""
        # Pre-flight checks
        if not self.pre_archive_checks(config):
            if self.window:
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
            tape_name = config.get('tape_name') or f"Tape_{device.replace('.', '').replace('\\', '')}" # Default if not provided
            mode = config['mode']
            copies = config['copies']
            compression = config['compression']
            index_files_flag = config.get('index_files', True)
            estimated_size = config.get('estimated_size', 0)
            file_count = config.get('file_count', 0)
            user_archive_name = config.get('archive_name')

            # Progress callback
            def progress_callback(data):
                if isinstance(data, dict):
                    if 'percent' in data:
                        self.update_progress(data['percent'], data.get('status', ''))
                    elif 'status' in data:
                        self.log_message(data['status'])
                    else:
                        self.log_message(str(data))
                else:
                    self.log_message(str(data))
            job_result_for_event_loop = {
                'success': False, 'error': None, 
                'archive_id': None, 'tape_id': None, 
                'mode': mode, 'tape_name': tape_name
            }

            try:
                db_manager = self.archive_manager.get_database_manager()

                if mode == ArchiveMode.STREAM:
                    job_result_for_event_loop['mode'] = 'stream'
                    try:
                        # 1. Ensure tape exists and get tape_id
                        tape_id = db_manager.add_tape_if_not_exists(tape_name, device, tape_status='active')
                        job_result_for_event_loop['tape_id'] = tape_id
                        if tape_id is None:
                            error_msg = f"Error: Could not get or create tape record for {tape_name} ({device})."
                            self.log_message(error_msg)
                            self.logger.error(f"Failed to get/create tape_id for {tape_name} on {device}")
                            job_result_for_event_loop['error'] = error_msg
                            raise Exception(error_msg) # Caught by outer try to set job_result and send JOB_DONE

                        # 2. Generate archive name
                        archive_name_to_save = user_archive_name or \
                                             self.archive_manager.generate_archive_name(folder_path, compression)

                        # 3. Add initial archive record with "streaming_to_tape" status
                        self.log_message(f"Creating initial archive record '{archive_name_to_save}' for streaming...")
                        initial_archive_id = db_manager.add_archive(
                            tape_id=tape_id,
                            archive_name=archive_name_to_save,
                            source_folder=folder_path,
                            size_bytes=estimated_size, # Using pre-calculated estimate
                            num_files=file_count,      # Using pre-calculated estimate
                            compression_enabled=compression,
                            status="streaming_to_tape", # Initial status
                            archive_checksum="PENDING_STREAM" # Placeholder checksum
                        )
                        job_result_for_event_loop['archive_id'] = initial_archive_id
                        self.current_archive_id = initial_archive_id # Keep track for this job instance

                        if initial_archive_id is None:
                            error_msg = f"Error: Failed to create initial archive record for {archive_name_to_save} on tape {tape_name}."
                            self.log_message(error_msg)
                            self.logger.error(error_msg)
                            job_result_for_event_loop['error'] = error_msg
                            raise Exception(error_msg) # Caught by outer try

                        self.log_message(f"Initial archive record ID {initial_archive_id} created with status 'streaming_to_tape'.")

                        # 4. Perform the streaming operation
                        self.log_message(f"Streaming {folder_path} to tape {device} (Tape: {tape_name}) for archive ID {initial_archive_id}...")
                        stream_result = self.tape_manager.stream_to_tape(
                            folder_path, device, compression, progress_callback
                        )

                        # 5. Process streaming result
                        if stream_result['success']:
                            self.log_message("Streaming completed successfully. Updating archive record...")
                            
                            actual_bytes = stream_result.get('bytes_written', estimated_size) 
                            actual_files = stream_result.get('files_processed', file_count) 
                            stream_checksum = stream_result.get('checksum', "STREAMED_UNVERIFIED")

                            update_success = db_manager.update_archive_status(
                                initial_archive_id, 
                                "completed",
                                new_checksum=stream_checksum,
                                new_size_bytes=actual_bytes,
                                new_num_files=actual_files
                            )
                            if update_success:
                                self.log_message(f"Archive ID {initial_archive_id} status updated to 'completed' with actual size/files.")
                            else:
                                self.log_message(f"Warning: Failed to update archive ID {initial_archive_id} status/details to 'completed'. DB record may be inconsistent.")

                            job_result_for_event_loop['success'] = True
                            
                            # 6. Index files if requested
                            if index_files_flag:
                                self.log_message(f"Indexing files for archive ID {initial_archive_id} ('{archive_name_to_save}')...")
                                try:
                                    self.archive_manager._index_archive_contents(folder_path, initial_archive_id, progress_callback=progress_callback)
                                    self.log_message("File indexing completed.")
                                except Exception as index_exc:
                                    self.log_message(f"Error during file indexing for archive ID {initial_archive_id}: {index_exc}")
                                    self.logger.error(f"File indexing error for archive {initial_archive_id}: {index_exc}", exc_info=True)
                                    # Don't mark job_result as failed overall, but log the indexing specific error
                            else:
                                self.log_message("File indexing skipped by user setting.")
                        
                        else: # Streaming failed
                            error_msg_stream = stream_result.get('error_message', "Unknown streaming error")
                            self.log_message(f"Streaming failed: {error_msg_stream}")
                            job_result_for_event_loop['error'] = f"Streaming failed: {error_msg_stream}"
                            job_result_for_event_loop['success'] = False # Ensure success is false
                            
                            update_failure_success = db_manager.update_archive_status(initial_archive_id, "streaming_failed")
                            if update_failure_success:
                                self.log_message(f"Archive ID {initial_archive_id} status updated to 'streaming_failed'.")
                            else:
                                self.log_message(f"Warning: Failed to update archive ID {initial_archive_id} status to 'streaming_failed'. DB record may be inconsistent.")

                        # 7. Handle second copy (placeholder)
                        if copies == 2 and job_result_for_event_loop['success']:
                            self.log_message("First stream copy successful. Second copy is a manual step or future feature.")
                            # self.handle_second_copy(folder_path, device, compression, progress_callback) # Placeholder call
                        elif copies == 2 and not job_result_for_event_loop['success']:
                            self.log_message("First stream copy failed, skipping second copy.")
                            
                    except Exception as stream_job_exc: # Catch exceptions within stream block
                        self.log_message(f"Critical error during streaming logic: {stream_job_exc}")
                        self.logger.error(f"Critical streaming logic error: {stream_job_exc}", exc_info=True)
                        job_result_for_event_loop['error'] = job_result_for_event_loop.get('error') or str(stream_job_exc)
                        job_result_for_event_loop['success'] = False
                        # This will be caught by the outer try/except if not already handled by JOB_DONE
                        # For now, this ensures job_result is populated before outer finally.

                else: # Cached Mode
                    job_result_for_event_loop['mode'] = 'cached'
                    self.log_message("Creating archive file (Cached Mode)...")
                    archive_info = self.archive_manager.create_cached_archive(
                        folder_path, 
                        compression=compression, 
                        progress_callback=progress_callback,
                        tape_label=tape_name, 
                        tape_device=device,
                        index_files=index_files_flag,
                        archive_name_override=user_archive_name
                    )
                    
                    job_result_for_event_loop['archive_id'] = archive_info.get('archive_id')
                    job_result_for_event_loop['tape_id'] = archive_info.get('tape_id')
                    self.current_archive_id = archive_info.get('archive_id')

                    archive_path = archive_info.get('archive_path')
                    checksum = archive_info.get('archive_checksum')

                    if archive_path and checksum and job_result_for_event_loop['archive_id'] is not None:
                        self.log_message(f"Archive created: {archive_path} (ID: {job_result_for_event_loop['archive_id']})")
                        self.log_message(f"Checksum: {checksum[:16]}...")
                        self.log_message(f"Writing archive to tape {device}")
                        write_success, bytes_written = self.tape_manager.write_archive_to_tape(
                            archive_path, device, progress_callback
                        )
                        
                        if write_success:
                            self.log_message(f"Archive written successfully ({bytes_written} bytes)")
                            job_result_for_event_loop['success'] = True
                            if copies == 2:
                                self.log_message("First cached copy successful. Second copy is a manual step or future feature.")
                                # self.handle_second_copy_cached(archive_path, device, progress_callback)
                        else:
                            self.log_message("Archive write to tape failed. Check tape and device.")
                            job_result_for_event_loop['error'] = "Archive write to tape failed."
                            job_result_for_event_loop['success'] = False
                    else:
                        err_msg = "Failed to create cached archive file, its database record, or retrieve archive ID. Check logs."
                        if not archive_path: err_msg = "Failed to create cached archive file (path missing)."
                        elif not checksum: err_msg = "Failed to create cached archive file (checksum missing)."
                        elif job_result_for_event_loop['archive_id'] is None: err_msg = "Failed to create/retrieve archive DB record for cached archive."
                        self.log_message(err_msg)
                        job_result_for_event_loop['error'] = err_msg
                        job_result_for_event_loop['success'] = False
                
                # Final job status update to UI before JOB_DONE signal
                if job_result_for_event_loop['success']:
                    self.update_progress(100, "Job completed successfully")
                    self.log_message("Archive job finished successfully.")
                else:
                    final_error_msg = job_result_for_event_loop.get('error', 'Job failed with unknown error')
                    self.update_progress(100, f"Job failed: {final_error_msg[:50]}...")
                    self.log_message(f"Archive job finished with errors: {final_error_msg}")
                
            except Exception as e:
                self.log_message(f"Unexpected error: {e}")
                job_result_for_event_loop['error'] = str(e)
                job_result_for_event_loop['success'] = False
            
            finally:
                self.window.write_event_value('-JOB_DONE-', job_result_for_event_loop)
