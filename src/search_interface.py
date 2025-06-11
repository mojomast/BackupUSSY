#!/usr/bin/env python3
"""
BackupUSSY Search Interface
GUI for searching and browsing archived content.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path

try:
    import FreeSimpleGUI as sg
except ImportError:
    print("FreeSimpleGUI not installed. Please run: pip install FreeSimpleGUI")
    exit(1)

from version import SEARCH_WINDOW_TITLE
from database_manager import DatabaseManager
from recovery_manager import RecoveryManager

logger = logging.getLogger(__name__)

class SearchInterface:
    """GUI interface for searching and browsing archived files."""
    
    def __init__(self, database_manager, recovery_manager=None):
        """Initialize search interface.
        
        Args:
            database_manager: DatabaseManager instance
            recovery_manager: Optional RecoveryManager for file recovery
        """
        self.db_manager = database_manager
        self.recovery_manager = recovery_manager
        self.search_window = None
        self.current_results = []
        
        logger.info("Search interface initialized")
    
    def create_search_window(self) -> sg.Window:
        """Create the main search window.
        
        Returns:
            PySimpleGUI Window object
        """
        # Search filters frame
        search_frame = [
            [sg.Text('Search Query:', size=(12, 1)), 
             sg.Input(key='-SEARCH_QUERY-', size=(40, 1)),
             sg.Button('Search', key='-SEARCH_BTN-')],
            [sg.Text('File Type:', size=(12, 1)),
             sg.Combo(['All Types', '.txt', '.jpg', '.png', '.pdf', '.doc', '.zip', '.mp4', '.mp3'], 
                     default_value='All Types', key='-FILE_TYPE-', size=(15, 1)),
             sg.Text('Tape:', size=(8, 1)),
             sg.Combo(['All Tapes'], key='-TAPE_FILTER-', size=(20, 1))],
            [sg.Text('Date Range:', size=(12, 1)),
             sg.Input(key='-DATE_FROM-', size=(12, 1)), sg.CalendarButton('From', target='-DATE_FROM-'),
             sg.Input(key='-DATE_TO-', size=(12, 1)), sg.CalendarButton('To', target='-DATE_TO-'),
             sg.Button('Clear Filters', key='-CLEAR_FILTERS-')]
        ]
        
        # Results display
        results_headings = ['File Path', 'Size', 'Modified', 'Archive', 'Tape', 'Type']
        results_frame = [
            [sg.Text(f'Search Results: 0 files found', key='-RESULTS_COUNT-')],
            [sg.Table(
                values=[],
                headings=results_headings,
                key='-RESULTS_TABLE-',
                auto_size_columns=False,
                col_widths=[40, 10, 15, 25, 15, 8],
                num_rows=15,
                alternating_row_color='lightblue',
                enable_events=True,
                select_mode=sg.TABLE_SELECT_MODE_EXTENDED
            )]
        ]
        
        # File details frame
        details_frame = [
            [sg.Text('Selected File Details:', font=('Arial', 10, 'bold'))],
            [sg.Multiline(size=(80, 8), key='-FILE_DETAILS-', disabled=True)]
        ]
        
        # Action buttons
        action_frame = [
            [sg.Button('Recover Selected Files', key='-RECOVER_FILES-', disabled=True),
             sg.Button('Show in Archive', key='-SHOW_ARCHIVE-', disabled=True),
             sg.Button('Export Results', key='-EXPORT_RESULTS-'),
             sg.Button('Advanced Search', key='-ADVANCED_SEARCH-')]
        ]
        
        # Main layout
        layout = [
            [sg.Frame('Search Criteria', search_frame, expand_x=True)],
            [sg.Frame('Search Results', results_frame, expand_x=True, expand_y=True)],
            [sg.Frame('File Details', details_frame, expand_x=True)],
            [sg.Frame('Actions', action_frame, expand_x=True)],
            [sg.Button('Close', key='-CLOSE-')]
        ]
        
        self.search_window = sg.Window(
            SEARCH_WINDOW_TITLE,
            layout,
            size=(1000, 700),
            resizable=True,
            finalize=True
        )
        
        # Initialize tape filter dropdown
        self._populate_tape_filter()
        
        return self.search_window
    
    def _populate_tape_filter(self):
        """Populate the tape filter dropdown with available tapes."""
        try:
            tapes = self.db_manager.get_all_tapes()
            tape_options = ['All Tapes'] + [f"{tape['tape_label']} ({tape['tape_device']})" for tape in tapes]
            self.search_window['-TAPE_FILTER-'].update(values=tape_options, value='All Tapes')
        except Exception as e:
            logger.error(f"Failed to populate tape filter: {e}")
    
    def search_files(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for files with given query and filters.
        
        Args:
            query: Search query string
            filters: Dictionary of search filters
            
        Returns:
            List of matching file records
        """
        try:
            logger.info(f"Searching for files with query: '{query}'")
            
            # Prepare search parameters
            file_type = filters.get('file_type') if filters else None
            if file_type == 'All Types':
                file_type = None
            
            tape_id = None
            if filters and filters.get('tape_label'):
                tape_label = filters['tape_label'].split(' (')[0]  # Extract label from dropdown text
                tape = self.db_manager.find_tape_by_label(tape_label)
                if tape:
                    tape_id = tape['tape_id']
            
            date_from = None
            date_to = None
            if filters:
                if filters.get('date_from'):
                    try:
                        date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d')
                    except ValueError:
                        pass
                if filters.get('date_to'):
                    try:
                        date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d')
                    except ValueError:
                        pass
            
            # Perform search
            results = self.db_manager.search(
                query=query,
                search_type='file',
                filters={
                    'file_type': file_type,
                    'tape_id': tape_id,
                    'date_from': date_from,
                    'date_to': date_to
                }
            )
            
            logger.info(f"Found {len(results)} matching files")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def display_search_results(self, results: List[Dict[str, Any]]):
        """Display search results in the table.
        
        Args:
            results: List of file records to display
        """
        self.current_results = results
        
        # Format results for table display
        table_data = []
        for result in results:
            # Format file size
            size_bytes = result.get('file_size_bytes', 0)
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                size_str = f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
            
            # Format date
            try:
                if result.get('file_modified'):
                    if isinstance(result['file_modified'], str):
                        date_obj = datetime.fromisoformat(result['file_modified'])
                    else:
                        date_obj = result['file_modified']
                    date_str = date_obj.strftime('%Y-%m-%d %H:%M')
                else:
                    date_str = 'Unknown'
            except (ValueError, AttributeError):
                date_str = 'Unknown'
            
            table_row = [
                result.get('file_path', ''),
                size_str,
                date_str,
                result.get('archive_name', ''),
                result.get('tape_label', ''),
                result.get('file_type', '')
            ]
            table_data.append(table_row)
        
        # Update table and counter
        if self.search_window:
            self.search_window['-RESULTS_TABLE-'].update(values=table_data)
            self.search_window['-RESULTS_COUNT-'].update(f'Search Results: {len(results)} files found')
            
            # Enable/disable action buttons based on results
            has_results = len(results) > 0
            self.search_window['-RECOVER_FILES-'].update(disabled=not has_results)
            self.search_window['-SHOW_ARCHIVE-'].update(disabled=not has_results)
    
    def show_file_details(self, file_indices: List[int]):
        """Show detailed information for selected files.
        
        Args:
            file_indices: List of selected file indices
        """
        if not file_indices or not self.current_results:
            self.search_window['-FILE_DETAILS-'].update('')
            return
        
        details_text = []
        
        for idx in file_indices:
            if 0 <= idx < len(self.current_results):
                file_info = self.current_results[idx]
                
                details_text.append(f"=== File {idx + 1} of {len(file_indices)} selected ===")
                details_text.append(f"Path: {file_info.get('file_path', 'Unknown')}")
                details_text.append(f"Size: {file_info.get('file_size_bytes', 0)} bytes")
                details_text.append(f"Modified: {file_info.get('file_modified', 'Unknown')}")
                details_text.append(f"Type: {file_info.get('file_type', 'Unknown')}")
                details_text.append(f"Archive: {file_info.get('archive_name', 'Unknown')}")
                details_text.append(f"Tape: {file_info.get('tape_label', 'Unknown')} ({file_info.get('tape_device', 'Unknown')})")
                details_text.append(f"Source Folder: {file_info.get('source_folder', 'Unknown')}")
                details_text.append(f"Archive Date: {file_info.get('archive_date', 'Unknown')}")
                details_text.append("")
        
        if self.search_window:
            self.search_window['-FILE_DETAILS-'].update('\n'.join(details_text))
    
    def recover_selected_files(self, file_indices: List[int], output_dir: str = None) -> bool:
        """Recover selected files from tape.
        
        Args:
            file_indices: List of selected file indices
            output_dir: Directory to recover files to
            
        Returns:
            True if recovery initiated successfully
        """
        if not file_indices or not self.current_results or not self.recovery_manager:
            return False
        
        try:
            # Get output directory if not provided
            if not output_dir:
                output_dir = sg.popup_get_folder('Select Recovery Directory')
                if not output_dir:
                    return False
            
            # Group files by tape and archive for efficient recovery
            recovery_groups = {}
            
            for idx in file_indices:
                if 0 <= idx < len(self.current_results):
                    file_info = self.current_results[idx]
                    tape_device = file_info.get('tape_device')
                    archive_name = file_info.get('archive_name')
                    
                    key = (tape_device, archive_name)
                    if key not in recovery_groups:
                        recovery_groups[key] = []
                    
                    recovery_groups[key].append(file_info['file_path'])
            
            # Start recovery process
            total_files = len(file_indices)
            recovered_files = 0
            
            for (tape_device, archive_name), file_paths in recovery_groups.items():
                logger.info(f"Recovering {len(file_paths)} files from {archive_name} on {tape_device}")
                
                # Create progress callback
                def progress_callback(data):
                    if data.get('type') == 'file_extracted':
                        nonlocal recovered_files
                        recovered_files += 1
                        sg.popup_quick_message(
                            f"Recovering files... {recovered_files}/{total_files}",
                            keep_on_top=True,
                            auto_close=True,
                            auto_close_duration=1
                        )
                
                # Recover files from this archive
                success = self.recovery_manager.extract_specific_files(
                    tape_device=tape_device,
                    archive_name=archive_name,
                    file_list=file_paths,
                    output_dir=output_dir,
                    progress_callback=progress_callback
                )
                
                if not success:
                    sg.popup_error(f"Failed to recover files from {archive_name}")
                    return False
            
            sg.popup(f"Successfully recovered {total_files} files to {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"File recovery failed: {e}")
            sg.popup_error(f"Recovery failed: {e}")
            return False
    
    def show_archive_contents(self, archive_id: int):
        """Show all files in a specific archive.
        
        Args:
            archive_id: Database ID of the archive
        """
        try:
            archive_details = self.db_manager.get_archive_details(archive_id)
            
            if not archive_details:
                sg.popup_error("Archive not found")
                return
            
            # Create archive browser window
            files = archive_details['files']
            archive_info = archive_details['archive_info']
            
            # Format file list for display
            file_data = []
            for file_info in files:
                size_bytes = file_info.get('file_size_bytes', 0)
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                
                file_data.append([
                    file_info.get('file_path', ''),
                    size_str,
                    file_info.get('file_type', ''),
                    file_info.get('file_modified', '')
                ])
            
            # Archive browser layout
            layout = [
                [sg.Text(f"Archive: {archive_info['archive_name']}", font=('Arial', 12, 'bold'))],
                [sg.Text(f"Source: {archive_info['source_folder']}")],
                [sg.Text(f"Tape: {archive_info['tape_label']} ({archive_info['tape_device']})")],
                [sg.Text(f"Files: {len(files)} | Size: {archive_info['archive_size_bytes']} bytes")],
                [sg.HSeparator()],
                [sg.Table(
                    values=file_data,
                    headings=['File Path', 'Size', 'Type', 'Modified'],
                    key='-ARCHIVE_FILES-',
                    auto_size_columns=False,
                    col_widths=[50, 12, 8, 20],
                    num_rows=20,
                    alternating_row_color='lightgray',
                    enable_events=True,
                    select_mode=sg.TABLE_SELECT_MODE_EXTENDED
                )],
                [sg.Button('Recover Selected', key='-RECOVER_ARCHIVE_FILES-'),
                 sg.Button('Recover All', key='-RECOVER_ALL_ARCHIVE-'),
                 sg.Button('Close', key='-CLOSE_ARCHIVE-')]
            ]
            
            archive_window = sg.Window(
                f'Archive Contents: {archive_info["archive_name"]}',
                layout,
                size=(800, 600),
                resizable=True,
                modal=True
            )
            
            # Handle archive browser events
            while True:
                event, values = archive_window.read()
                
                if event in (sg.WIN_CLOSED, '-CLOSE_ARCHIVE-'):
                    break
                elif event == '-RECOVER_ALL_ARCHIVE-':
                    # Recover entire archive
                    output_dir = sg.popup_get_folder('Select Recovery Directory')
                    if output_dir and self.recovery_manager:
                        success = self.recovery_manager.extract_archive(
                            tape_device=archive_info['tape_device'],
                            archive_name=archive_info['archive_name'],
                            output_dir=output_dir
                        )
                        if success:
                            sg.popup(f"Archive recovered to {output_dir}")
                        else:
                            sg.popup_error("Archive recovery failed")
                elif event == '-RECOVER_ARCHIVE_FILES-':
                    # Recover selected files from archive
                    selected_rows = values['-ARCHIVE_FILES-']
                    if selected_rows:
                        file_paths = [files[i]['file_path'] for i in selected_rows]
                        output_dir = sg.popup_get_folder('Select Recovery Directory')
                        if output_dir and self.recovery_manager:
                            success = self.recovery_manager.extract_specific_files(
                                tape_device=archive_info['tape_device'],
                                archive_name=archive_info['archive_name'],
                                file_list=file_paths,
                                output_dir=output_dir
                            )
                            if success:
                                sg.popup(f"Selected files recovered to {output_dir}")
                            else:
                                sg.popup_error("File recovery failed")
            
            archive_window.close()
            
        except Exception as e:
            logger.error(f"Failed to show archive contents: {e}")
            sg.popup_error(f"Failed to show archive: {e}")
    
    def export_search_results(self, results: List[Dict[str, Any]], output_file: str = None) -> bool:
        """Export search results to CSV file.
        
        Args:
            results: Search results to export
            output_file: Output file path
            
        Returns:
            True if export successful
        """
        try:
            if not output_file:
                output_file = sg.popup_get_file(
                    'Save search results as...',
                    save_as=True,
                    file_types=(('CSV Files', '*.csv'), ('All Files', '*.*')),
                    default_extension='.csv'
                )
                if not output_file:
                    return False
            
            import csv
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'File Path', 'File Size (bytes)', 'Modified Date', 'File Type',
                    'Archive Name', 'Tape Label', 'Tape Device', 'Source Folder',
                    'Archive Date', 'Archive ID', 'Tape ID'
                ])
                
                # Write data
                for result in results:
                    writer.writerow([
                        result.get('file_path', ''),
                        result.get('file_size_bytes', 0),
                        result.get('file_modified', ''),
                        result.get('file_type', ''),
                        result.get('archive_name', ''),
                        result.get('tape_label', ''),
                        result.get('tape_device', ''),
                        result.get('source_folder', ''),
                        result.get('archive_date', ''),
                        result.get('archive_id', ''),
                        result.get('tape_id', '')
                    ])
            
            logger.info(f"Exported {len(results)} search results to {output_file}")
            sg.popup(f"Search results exported to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            sg.popup_error(f"Export failed: {e}")
            return False
    
    def run_search_interface(self):
        """Run the search interface main loop."""
        if not self.search_window:
            self.create_search_window()
        
        logger.info("Starting search interface")
        
        while True:
            event, values = self.search_window.read()
            
            if event in (sg.WIN_CLOSED, '-CLOSE-'):
                break
            
            elif event == '-SEARCH_BTN-':
                # Perform search
                query = values['-SEARCH_QUERY-'].strip()
                if not query:
                    sg.popup('Please enter a search query')
                    continue
                
                filters = {
                    'file_type': values['-FILE_TYPE-'],
                    'tape_label': values['-TAPE_FILTER-'] if values['-TAPE_FILTER-'] != 'All Tapes' else None,
                    'date_from': values['-DATE_FROM-'],
                    'date_to': values['-DATE_TO-']
                }
                
                results = self.search_files(query, filters)
                self.display_search_results(results)
            
            elif event == '-CLEAR_FILTERS-':
                # Clear all search filters
                self.search_window['-SEARCH_QUERY-'].update('')
                self.search_window['-FILE_TYPE-'].update('All Types')
                self.search_window['-TAPE_FILTER-'].update('All Tapes')
                self.search_window['-DATE_FROM-'].update('')
                self.search_window['-DATE_TO-'].update('')
                self.search_window['-RESULTS_TABLE-'].update(values=[])
                self.search_window['-RESULTS_COUNT-'].update('Search Results: 0 files found')
                self.search_window['-FILE_DETAILS-'].update('')
                self.current_results = []
            
            elif event == '-RESULTS_TABLE-':
                # Table selection changed
                selected_rows = values['-RESULTS_TABLE-']
                self.show_file_details(selected_rows)
            
            elif event == '-RECOVER_FILES-':
                # Recover selected files
                selected_rows = values['-RESULTS_TABLE-']
                if selected_rows:
                    self.recover_selected_files(selected_rows)
                else:
                    sg.popup('Please select files to recover')
            
            elif event == '-SHOW_ARCHIVE-':
                # Show archive contents
                selected_rows = values['-RESULTS_TABLE-']
                if selected_rows and self.current_results:
                    file_info = self.current_results[selected_rows[0]]
                    archive_id = file_info.get('archive_id')
                    if archive_id:
                        self.show_archive_contents(archive_id)
                else:
                    sg.popup('Please select a file first')
            
            elif event == '-EXPORT_RESULTS-':
                # Export search results
                if self.current_results:
                    self.export_search_results(self.current_results)
                else:
                    sg.popup('No search results to export')
            
            elif event == '-ADVANCED_SEARCH-':
                # Show advanced search options
                sg.popup('Advanced search features coming soon!',
                        'Features planned:\n'
                        '- Regular expression search\n'
                        '- File size filters\n'
                        '- Multiple file type selection\n'
                        '- Duplicate file detection\n'
                        '- Search within archives')
        
        self.search_window.close()
        logger.info("Search interface closed")


def main():
    """Main function for testing search interface."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Initialize components
        db_manager = DatabaseManager()
        recovery_manager = RecoveryManager(db_manager)
        
        # Create and run search interface
        search_interface = SearchInterface(db_manager, recovery_manager)
        search_interface.run_search_interface()
        
    except Exception as e:
        sg.popup_error(f"Search interface failed: {e}")
        logging.error(f"Search interface error: {e}")


if __name__ == '__main__':
    main()

