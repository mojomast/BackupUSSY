#!/usr/bin/env python3
"""
BackupUSSY Tape Browser
Hierarchical browsing interface for LTO tape library management.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

try:
    import FreeSimpleGUI as sg
except ImportError:
    print("FreeSimpleGUI not installed. Please run: pip install FreeSimpleGUI")
    exit(1)

from version import BROWSER_WINDOW_TITLE
from database_manager import DatabaseManager
from recovery_manager import RecoveryManager

logger = logging.getLogger(__name__)

class TapeBrowser:
    """Hierarchical browser for tapes, archives, and files."""
    
    def __init__(self, database_manager, recovery_manager=None):
        """Initialize tape browser.
        
        Args:
            database_manager: DatabaseManager instance
            recovery_manager: Optional RecoveryManager for file recovery
        """
        self.db_manager = database_manager
        self.recovery_manager = recovery_manager
        self.browser_window = None
        self.tree_data = None
        self.current_selection = None
        
        logger.info("Tape browser initialized")
    
    def create_browser_window(self) -> sg.Window:
        """Create the main browser window.
        
        Returns:
            PySimpleGUI Window object
        """
        # Tree view for hierarchical navigation
        tree_frame = [
            [sg.Text('Tape Library Browser', font=('Arial', 12, 'bold'))],
            [sg.Tree(
                data=self._build_tree_data(),
                headings=['Type', 'Size', 'Files', 'Date'],
                auto_size_columns=True,
                col_widths=[15, 12, 8, 15],
                num_rows=20,
                col0_width=40,
                key='-TREE-',
                show_expanded=False,
                enable_events=True,
                expand_x=True,
                expand_y=True
            )]
        ]
        
        # Information panel
        info_frame = [
            [sg.Text('Selected Item Details:', font=('Arial', 10, 'bold'))],
            [sg.Multiline(
                size=(50, 8),
                key='-INFO_PANEL-',
                disabled=True,
                expand_x=True
            )]
        ]
        
        # Statistics panel
        stats_frame = [
            [sg.Text('Library Statistics:', font=('Arial', 10, 'bold'))],
            [sg.Text('Tapes:', size=(12, 1)), sg.Text('0', key='-STAT_TAPES-')],
            [sg.Text('Archives:', size=(12, 1)), sg.Text('0', key='-STAT_ARCHIVES-')],
            [sg.Text('Total Files:', size=(12, 1)), sg.Text('0', key='-STAT_FILES-')],
            [sg.Text('Total Size:', size=(12, 1)), sg.Text('0 GB', key='-STAT_SIZE-')],
            [sg.HSeparator()],
            [sg.Text('Selected Item:', font=('Arial', 9, 'bold'))],
            [sg.Text('Type:', size=(8, 1)), sg.Text('None', key='-SEL_TYPE-')],
            [sg.Text('Size:', size=(8, 1)), sg.Text('N/A', key='-SEL_SIZE-')],
            [sg.Text('Files:', size=(8, 1)), sg.Text('N/A', key='-SEL_FILES-')]
        ]
        
        # Action buttons
        action_frame = [
            [sg.Button('Refresh', key='-REFRESH-'),
             sg.Button('Expand All', key='-EXPAND_ALL-'),
             sg.Button('Collapse All', key='-COLLAPSE_ALL-')],
            [sg.HSeparator()],
            [sg.Button('View Archive', key='-VIEW_ARCHIVE-', disabled=True),
             sg.Button('Recover Files', key='-RECOVER_SELECTION-', disabled=True),
             sg.Button('Search in Selection', key='-SEARCH_SELECTION-', disabled=True)],
            [sg.HSeparator()],
            [sg.Button('Tape Properties', key='-TAPE_PROPS-', disabled=True),
             sg.Button('Export List', key='-EXPORT_LIST-'),
             sg.Button('Generate Report', key='-GENERATE_REPORT-')]
        ]
        
        # Filter controls
        filter_frame = [
            [sg.Text('Filters:', font=('Arial', 10, 'bold'))],
            [sg.Text('Status:', size=(8, 1)),
             sg.Combo(['All', 'Active', 'Full', 'Damaged', 'Retired'], 
                     default_value='All', key='-FILTER_STATUS-', size=(10, 1),
                     enable_events=True)],
            [sg.Text('Date:', size=(8, 1)),
             sg.Combo(['All Time', 'Last Week', 'Last Month', 'Last Year'], 
                     default_value='All Time', key='-FILTER_DATE-', size=(12, 1),
                     enable_events=True)],
            [sg.Checkbox('Show Empty Tapes', key='-SHOW_EMPTY-', default=True, enable_events=True)]
        ]
        
        # Layout with splitter
        left_column = [
            [sg.Frame('Library Tree', tree_frame, expand_x=True, expand_y=True)]
        ]
        
        right_column = [
            [sg.Frame('Statistics', stats_frame)],
            [sg.Frame('Filters', filter_frame)],
            [sg.Frame('Actions', action_frame)],
            [sg.Frame('Information', info_frame, expand_x=True, expand_y=True)]
        ]
        
        layout = [
            [sg.Column(left_column, size=(600, 600), expand_x=True, expand_y=True),
             sg.VSeperator(),
             sg.Column(right_column, size=(350, 600), expand_y=True)],
            [sg.StatusBar('Ready', key='-STATUS-', size=(80, 1))],
            [sg.Button('Close', key='-CLOSE-')]
        ]
        
        self.browser_window = sg.Window(
            BROWSER_WINDOW_TITLE,
            layout,
            size=(1000, 700),
            resizable=True,
            finalize=True
        )
        
        # Load initial statistics
        self._update_statistics()
        
        return self.browser_window
    
    def _build_tree_data(self) -> sg.TreeData:
        """Build the hierarchical tree data structure.
        
        Returns:
            TreeData object for the tree view
        """
        try:
            tree_data = sg.TreeData()
            
            # Get all tapes
            tapes = self.db_manager.get_all_tapes()
            
            for tape in tapes:
                tape_id = tape['tape_id']
                tape_key = f"tape_{tape_id}"
                
                # Format tape node
                tape_size_gb = (tape.get('total_size_bytes', 0) or 0) / (1024**3)
                tape_status = tape.get('tape_status', 'unknown')
                
                # Get tape archive count
                archives = self.db_manager.get_tape_contents(tape_id)
                archive_count = len(archives)
                
                # Format tape display
                tape_text = f"{tape['tape_label']} [{tape_status}]"
                tape_values = ['Tape', f"{tape_size_gb:.1f} GB", f"{archive_count} archives", 
                              tape.get('created_date', 'Unknown')[:10] if tape.get('created_date') else 'Unknown']
                
                # Add tape node
                tree_data.Insert(
                    parent='',
                    key=tape_key,
                    text=tape_text,
                    values=tape_values,
                    icon=self._get_tape_icon(tape_status)
                )
                
                # Add archives under this tape
                for archive in archives:
                    archive_id = archive['archive_id']
                    archive_key = f"archive_{archive_id}"
                    
                    # Format archive node
                    archive_size_mb = (archive.get('archive_size_bytes', 0) or 0) / (1024**2)
                    file_count = archive.get('file_count', 0) or 0
                    
                    archive_text = archive['archive_name']
                    archive_values = ['Archive', f"{archive_size_mb:.1f} MB", f"{file_count} files",
                                    archive.get('archive_date', 'Unknown')[:10] if archive.get('archive_date') else 'Unknown']
                    
                    # Add archive node
                    tree_data.Insert(
                        parent=tape_key,
                        key=archive_key,
                        text=archive_text,
                        values=archive_values,
                        icon=self._get_archive_icon()
                    )
                    
                    # Add folder structure under archive (limited depth for performance)
                    self._add_folder_structure(tree_data, archive_key, archive_id)
            
            self.tree_data = tree_data
            return tree_data
            
        except Exception as e:
            logger.error(f"Failed to build tree data: {e}")
            return sg.TreeData()  # Return empty tree
    
    def _add_folder_structure(self, tree_data: sg.TreeData, parent_key: str, archive_id: int):
        """Add folder structure under an archive node.
        
        Args:
            tree_data: TreeData object to modify
            parent_key: Parent archive key
            archive_id: Archive ID to get files from
        """
        try:
            # Get files for this archive
            files = self.db_manager.get_archive_files(archive_id)
            
            # Group files by top-level folder
            folders = {}
            for file_info in files:
                file_path = file_info['file_path']
                path_parts = file_path.split('/')  # Assuming Unix-style paths
                
                if len(path_parts) > 1:
                    # Has folders
                    top_folder = path_parts[0]
                    if top_folder not in folders:
                        folders[top_folder] = []
                    folders[top_folder].append(file_info)
                else:
                    # Root file
                    if '__root__' not in folders:
                        folders['__root__'] = []
                    folders['__root__'].append(file_info)
            
            # Add folder nodes (limit to prevent UI slowdown)
            max_folders = 20
            folder_count = 0
            
            for folder_name, folder_files in folders.items():
                if folder_count >= max_folders:
                    # Add "...more" node
                    more_key = f"{parent_key}_more"
                    tree_data.Insert(
                        parent=parent_key,
                        key=more_key,
                        text=f"... and {len(folders) - max_folders} more folders",
                        values=['Folder', '', f"{len(files) - sum(len(f) for f in list(folders.values())[:max_folders])} files", ''],
                        icon='📁'
                    )
                    break
                
                folder_key = f"{parent_key}_folder_{folder_name}"
                
                # Calculate folder stats
                folder_size = sum(f.get('file_size_bytes', 0) for f in folder_files)
                folder_size_mb = folder_size / (1024**2) if folder_size else 0
                
                display_name = folder_name if folder_name != '__root__' else '(root files)'
                
                folder_values = ['Folder', f"{folder_size_mb:.1f} MB", f"{len(folder_files)} files", '']
                
                tree_data.Insert(
                    parent=parent_key,
                    key=folder_key,
                    text=display_name,
                    values=folder_values,
                    icon='📁'
                )
                
                # Add some files under folder (limited for performance)
                max_files_shown = 10
                for i, file_info in enumerate(folder_files[:max_files_shown]):
                    file_key = f"{folder_key}_file_{file_info['file_id']}"
                    
                    file_size_kb = (file_info.get('file_size_bytes', 0) or 0) / 1024
                    file_name = os.path.basename(file_info['file_path'])
                    
                    file_values = ['File', f"{file_size_kb:.1f} KB", '1 file', 
                                 file_info.get('file_modified', 'Unknown')[:10] if file_info.get('file_modified') else 'Unknown']
                    
                    tree_data.Insert(
                        parent=folder_key,
                        key=file_key,
                        text=file_name,
                        values=file_values,
                        icon=self._get_file_icon(file_info.get('file_type', ''))
                    )
                
                # Add "...more files" if needed
                if len(folder_files) > max_files_shown:
                    more_files_key = f"{folder_key}_more_files"
                    tree_data.Insert(
                        parent=folder_key,
                        key=more_files_key,
                        text=f"... and {len(folder_files) - max_files_shown} more files",
                        values=['', '', '', ''],
                        icon='📄'
                    )
                
                folder_count += 1
                
        except Exception as e:
            logger.error(f"Failed to add folder structure for archive {archive_id}: {e}")
    
    def _get_tape_icon(self, status: str) -> str:
        """Get icon for tape based on status."""
        icons = {
            'active': '🟢',
            'full': '🔴',
            'damaged': '⚠️',
            'retired': '⚫',
            'unknown': '❓'
        }
        return icons.get(status.lower(), '❓')
    
    def _get_archive_icon(self) -> str:
        """Get icon for archive nodes."""
        return '📦'
    
    def _get_file_icon(self, file_type: str) -> str:
        """Get icon based on file type."""
        icons = {
            '.txt': '📄',
            '.pdf': '📕',
            '.jpg': '🖼️',
            '.png': '🖼️',
            '.gif': '🖼️',
            '.mp4': '🎬',
            '.mp3': '🎵',
            '.zip': '📦',
            '.rar': '📦',
            '.doc': '📝',
            '.docx': '📝',
            '.xls': '📊',
            '.xlsx': '📊'
        }
        return icons.get(file_type.lower(), '📄')
    
    def _update_statistics(self):
        """Update the statistics panel."""
        try:
            # Get overall statistics
            tapes = self.db_manager.get_all_tapes()
            
            total_archives = 0
            total_files = 0
            total_size = 0
            
            for tape in tapes:
                archives = self.db_manager.get_tape_contents(tape['tape_id'])
                total_archives += len(archives)
                
                for archive in archives:
                    total_files += archive.get('file_count', 0) or 0
                    total_size += archive.get('archive_size_bytes', 0) or 0
            
            # Update display
            if self.browser_window:
                self.browser_window['-STAT_TAPES-'].update(str(len(tapes)))
                self.browser_window['-STAT_ARCHIVES-'].update(str(total_archives))
                self.browser_window['-STAT_FILES-'].update(f"{total_files:,}")
                self.browser_window['-STAT_SIZE-'].update(f"{total_size / (1024**3):.1f} GB")
                
        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")
    
    def _update_selection_info(self, selected_key: str):
        """Update information panel for selected item.
        
        Args:
            selected_key: Key of selected tree item
        """
        try:
            if not selected_key:
                self._clear_selection_info()
                return
            
            self.current_selection = selected_key
            info_text = []
            sel_type = 'None'
            sel_size = 'N/A'
            sel_files = 'N/A'
            
            if selected_key.startswith('tape_'):
                # Tape selected
                tape_id = int(selected_key.split('_')[1])
                tape_info = self.db_manager.get_tape_info(tape_id)
                
                if tape_info:
                    sel_type = 'Tape'
                    sel_size = f"{(tape_info.get('total_size_bytes', 0) or 0) / (1024**3):.1f} GB"
                    
                    archives = self.db_manager.get_tape_contents(tape_id)
                    archive_count = len(archives)
                    total_files = sum(a.get('file_count', 0) or 0 for a in archives)
                    sel_files = f"{archive_count} archives, {total_files} files"
                    
                    info_text.extend([
                        f"Tape Label: {tape_info['tape_label']}",
                        f"Device: {tape_info.get('tape_device', 'Unknown')}",
                        f"Status: {tape_info.get('tape_status', 'Unknown')}",
                        f"Created: {tape_info.get('created_date', 'Unknown')}",
                        f"Last Written: {tape_info.get('last_written', 'Unknown')}",
                        f"Total Size: {sel_size}",
                        f"Archives: {archive_count}",
                        f"Total Files: {total_files:,}",
                        f"Compression: {'Yes' if tape_info.get('compression_used') else 'No'}",
                        "",
                        "Notes:",
                        tape_info.get('notes', 'No notes')
                    ])
            
            elif selected_key.startswith('archive_'):
                # Archive selected
                archive_id = int(selected_key.split('_')[1])
                archive_details = self.db_manager.get_archive_details(archive_id)
                
                if archive_details:
                    archive_info = archive_details['archive_info']
                    files = archive_details['files']
                    
                    sel_type = 'Archive'
                    sel_size = f"{(archive_info.get('archive_size_bytes', 0) or 0) / (1024**2):.1f} MB"
                    sel_files = f"{len(files)} files"
                    
                    info_text.extend([
                        f"Archive Name: {archive_info['archive_name']}",
                        f"Source Folder: {archive_info['source_folder']}",
                        f"Created: {archive_info.get('archive_date', 'Unknown')}",
                        f"Size: {sel_size}",
                        f"File Count: {len(files)}",
                        f"Tape: {archive_info.get('tape_label', 'Unknown')}",
                        f"Position: {archive_info.get('archive_position', 'Unknown')}",
                        f"Checksum: {archive_info.get('checksum', 'Not available')[:16]}...",
                        f"Compression: {'Yes' if archive_info.get('compression_used') else 'No'}",
                        "",
                        "File Types:"
                    ])
                    
                    # Show file type distribution
                    file_types = {}
                    for file_info in files:
                        file_type = file_info.get('file_type', 'unknown')
                        file_types[file_type] = file_types.get(file_type, 0) + 1
                    
                    for file_type, count in sorted(file_types.items()):
                        info_text.append(f"  {file_type}: {count} files")
            
            elif selected_key.startswith('archive_') and '_folder_' in selected_key:
                # Folder selected
                sel_type = 'Folder'
                info_text.append("Selected folder in archive")
                info_text.append("Use 'View Archive' to see all files")
            
            elif selected_key.startswith('archive_') and '_file_' in selected_key:
                # Individual file selected
                parts = selected_key.split('_')
                if len(parts) >= 4:
                    try:
                        file_id = int(parts[-1])
                        file_info = self.db_manager.get_file_details(file_id)
                        
                        if file_info:
                            sel_type = 'File'
                            sel_size = f"{(file_info.get('file_size_bytes', 0) or 0) / 1024:.1f} KB"
                            sel_files = '1 file'
                            
                            info_text.extend([
                                f"File Path: {file_info['file_path']}",
                                f"Size: {sel_size}",
                                f"Type: {file_info.get('file_type', 'Unknown')}",
                                f"Modified: {file_info.get('file_modified', 'Unknown')}",
                                f"Archive: {file_info.get('archive_name', 'Unknown')}",
                                f"Tape: {file_info.get('tape_label', 'Unknown')}",
                                f"Checksum: {file_info.get('file_checksum', 'Not available')}"
                            ])
                    except (ValueError, IndexError):
                        pass
            
            # Update UI
            if self.browser_window:
                self.browser_window['-INFO_PANEL-'].update('\n'.join(info_text))
                self.browser_window['-SEL_TYPE-'].update(sel_type)
                self.browser_window['-SEL_SIZE-'].update(sel_size)
                self.browser_window['-SEL_FILES-'].update(sel_files)
                
                # Update button states
                is_tape = selected_key.startswith('tape_')
                is_archive = selected_key.startswith('archive_') and '_folder_' not in selected_key and '_file_' not in selected_key
                is_recoverable = is_archive or (selected_key.startswith('archive_') and ('_folder_' in selected_key or '_file_' in selected_key))
                
                self.browser_window['-VIEW_ARCHIVE-'].update(disabled=not is_archive)
                self.browser_window['-RECOVER_SELECTION-'].update(disabled=not is_recoverable)
                self.browser_window['-SEARCH_SELECTION-'].update(disabled=not (is_tape or is_archive))
                self.browser_window['-TAPE_PROPS-'].update(disabled=not is_tape)
                
        except Exception as e:
            logger.error(f"Failed to update selection info: {e}")
    
    def _clear_selection_info(self):
        """Clear selection information."""
        if self.browser_window:
            self.browser_window['-INFO_PANEL-'].update('')
            self.browser_window['-SEL_TYPE-'].update('None')
            self.browser_window['-SEL_SIZE-'].update('N/A')
            self.browser_window['-SEL_FILES-'].update('N/A')
            
            # Disable action buttons
            self.browser_window['-VIEW_ARCHIVE-'].update(disabled=True)
            self.browser_window['-RECOVER_SELECTION-'].update(disabled=True)
            self.browser_window['-SEARCH_SELECTION-'].update(disabled=True)
            self.browser_window['-TAPE_PROPS-'].update(disabled=True)
    
    def _apply_filters(self):
        """Apply current filters and refresh tree."""
        try:
            # Get filter values
            status_filter = None
            if self.browser_window:
                filter_status = self.browser_window['-FILTER_STATUS-'].get()
                if filter_status != 'All':
                    status_filter = filter_status.lower()
            
            # Rebuild tree with filters (this is a simplified implementation)
            self.browser_window['-TREE-'].update(values=self._build_tree_data())
            self.browser_window['-STATUS-'].update('Filters applied')
            
        except Exception as e:
            logger.error(f"Failed to apply filters: {e}")
    
    def view_archive_contents(self, archive_id: int):
        """Open detailed archive view window.
        
        Args:
            archive_id: ID of archive to view
        """
        try:
            # This would integrate with the search interface's archive browser
            from search_interface import SearchInterface
            
            search_interface = SearchInterface(self.db_manager, self.recovery_manager)
            search_interface.show_archive_contents(archive_id)
            
        except Exception as e:
            logger.error(f"Failed to view archive contents: {e}")
            sg.popup_error(f"Failed to view archive: {e}")
    
    def recover_selection(self):
        """Recover the currently selected item."""
        if not self.current_selection or not self.recovery_manager:
            return
        
        try:
            if self.current_selection.startswith('archive_'):
                archive_id = int(self.current_selection.split('_')[1])
                archive_details = self.db_manager.get_archive_details(archive_id)
                
                if archive_details:
                    archive_info = archive_details['archive_info']
                    
                    output_dir = sg.popup_get_folder('Select recovery directory:')
                    if output_dir:
                        success = self.recovery_manager.extract_archive(
                            tape_device=archive_info['tape_device'],
                            archive_name=archive_info['archive_name'],
                            output_dir=output_dir
                        )
                        
                        if success:
                            sg.popup(f"Archive recovered to {output_dir}")
                        else:
                            sg.popup_error("Archive recovery failed")
            
            else:
                sg.popup('Recovery not implemented for this item type')
                
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            sg.popup_error(f"Recovery failed: {e}")
    
    def export_list(self):
        """Export current view to CSV."""
        try:
            import csv
            
            output_file = sg.popup_get_file(
                'Save list as...',
                save_as=True,
                file_types=(('CSV Files', '*.csv'), ('All Files', '*.*')),
                default_extension='.csv'
            )
            
            if not output_file:
                return
            
            # Export all tapes and archives
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Type', 'Name', 'Size (Bytes)', 'File Count', 'Date', 'Status', 'Parent'
                ])
                
                # Write tape data
                tapes = self.db_manager.get_all_tapes()
                for tape in tapes:
                    writer.writerow([
                        'Tape',
                        tape['tape_label'],
                        tape.get('total_size_bytes', 0),
                        '',  # File count calculated differently for tapes
                        tape.get('created_date', ''),
                        tape.get('tape_status', ''),
                        ''
                    ])
                    
                    # Write archives for this tape
                    archives = self.db_manager.get_tape_contents(tape['tape_id'])
                    for archive in archives:
                        writer.writerow([
                            'Archive',
                            archive['archive_name'],
                            archive.get('archive_size_bytes', 0),
                            archive.get('file_count', 0),
                            archive.get('archive_date', ''),
                            '',
                            tape['tape_label']
                        ])
            
            sg.popup(f"List exported to {output_file}")
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            sg.popup_error(f"Export failed: {e}")
    
    def run_browser_interface(self):
        """Run the tape browser main loop."""
        if not self.browser_window:
            self.create_browser_window()
        
        logger.info("Starting tape browser interface")
        
        while True:
            event, values = self.browser_window.read()
            
            if event in (sg.WIN_CLOSED, '-CLOSE-'):
                break
            
            elif event == '-TREE-':
                # Tree selection changed
                selected_items = values['-TREE-']
                if selected_items:
                    selected_key = selected_items[0]
                    self._update_selection_info(selected_key)
                else:
                    self._clear_selection_info()
            
            elif event == '-REFRESH-':
                # Refresh tree data
                self.browser_window['-TREE-'].update(values=self._build_tree_data())
                self._update_statistics()
                self.browser_window['-STATUS-'].update('Refreshed')
            
            elif event == '-EXPAND_ALL-':
                # Expand all tree nodes
                if self.tree_data:
                    self.browser_window['-TREE-'].expand()
                self.browser_window['-STATUS-'].update('Expanded all')
            
            elif event == '-COLLAPSE_ALL-':
                # Collapse all tree nodes
                if self.tree_data:
                    # PySimpleGUI doesn't have a direct collapse_all, so we rebuild
                    self.browser_window['-TREE-'].update(values=self._build_tree_data())
                self.browser_window['-STATUS-'].update('Collapsed all')
            
            elif event in ['-FILTER_STATUS-', '-FILTER_DATE-', '-SHOW_EMPTY-']:
                # Filter changed
                self._apply_filters()
            
            elif event == '-VIEW_ARCHIVE-':
                # View archive contents
                if self.current_selection and self.current_selection.startswith('archive_'):
                    archive_id = int(self.current_selection.split('_')[1])
                    self.view_archive_contents(archive_id)
            
            elif event == '-RECOVER_SELECTION-':
                # Recover selected item
                self.recover_selection()
            
            elif event == '-SEARCH_SELECTION-':
                # Search within selection
                sg.popup('Search functionality would integrate with search interface')
            
            elif event == '-TAPE_PROPS-':
                # Show tape properties
                if self.current_selection and self.current_selection.startswith('tape_'):
                    tape_id = int(self.current_selection.split('_')[1])
                    self._show_tape_properties(tape_id)
            
            elif event == '-EXPORT_LIST-':
                # Export current list
                self.export_list()
            
            elif event == '-GENERATE_REPORT-':
                # Generate library report
                self._generate_library_report()
        
        self.browser_window.close()
        logger.info("Tape browser interface closed")
    
    def _show_tape_properties(self, tape_id: int):
        """Show tape properties dialog.
        
        Args:
            tape_id: ID of tape to show properties for
        """
        try:
            tape_info = self.db_manager.get_tape_info(tape_id)
            if not tape_info:
                sg.popup_error("Tape not found")
                return
            
            # Create properties dialog
            layout = [
                [sg.Text(f"Properties for Tape: {tape_info['tape_label']}", font=('Arial', 12, 'bold'))],
                [sg.HSeparator()],
                [sg.Text('Label:', size=(15, 1)), sg.Input(tape_info['tape_label'], key='-TAPE_LABEL-')],
                [sg.Text('Device:', size=(15, 1)), sg.Text(tape_info.get('tape_device', 'Unknown'))],
                [sg.Text('Status:', size=(15, 1)), 
                 sg.Combo(['active', 'full', 'damaged', 'retired'], 
                         default_value=tape_info.get('tape_status', 'active'), key='-TAPE_STATUS-')],
                [sg.Text('Created:', size=(15, 1)), sg.Text(tape_info.get('created_date', 'Unknown'))],
                [sg.Text('Last Written:', size=(15, 1)), sg.Text(tape_info.get('last_written', 'Unknown'))],
                [sg.Text('Total Size:', size=(15, 1)), 
                 sg.Text(f"{(tape_info.get('total_size_bytes', 0) or 0) / (1024**3):.2f} GB")],
                [sg.Text('Notes:', size=(15, 1))],
                [sg.Multiline(tape_info.get('notes', ''), key='-TAPE_NOTES-', size=(50, 5))],
                [sg.HSeparator()],
                [sg.Button('Save', key='-SAVE_PROPS-'), sg.Button('Cancel', key='-CANCEL_PROPS-')]
            ]
            
            props_window = sg.Window(
                'Tape Properties',
                layout,
                modal=True,
                resizable=True
            )
            
            while True:
                event, values = props_window.read()
                
                if event in (sg.WIN_CLOSED, '-CANCEL_PROPS-'):
                    break
                elif event == '-SAVE_PROPS-':
                    # Save changes
                    try:
                        self.db_manager.update_tape_info(
                            tape_id=tape_id,
                            tape_label=values['-TAPE_LABEL-'],
                            tape_status=values['-TAPE_STATUS-'],
                            notes=values['-TAPE_NOTES-']
                        )
                        sg.popup('Tape properties saved')
                        
                        # Refresh browser
                        self.browser_window['-TREE-'].update(values=self._build_tree_data())
                        break
                        
                    except Exception as e:
                        sg.popup_error(f"Failed to save properties: {e}")
            
            props_window.close()
            
        except Exception as e:
            logger.error(f"Failed to show tape properties: {e}")
            sg.popup_error(f"Failed to show properties: {e}")
    
    def _generate_library_report(self):
        """Generate a comprehensive library report."""
        try:
            from datetime import datetime
            
            # Generate report data
            tapes = self.db_manager.get_all_tapes()
            report_lines = []
            
            report_lines.append("LTO TAPE LIBRARY REPORT")
            report_lines.append("=" * 50)
            report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")
            
            # Summary statistics
            total_tapes = len(tapes)
            total_size = sum((t.get('total_size_bytes', 0) or 0) for t in tapes)
            active_tapes = len([t for t in tapes if t.get('tape_status') == 'active'])
            
            report_lines.extend([
                "SUMMARY STATISTICS:",
                f"Total Tapes: {total_tapes}",
                f"Active Tapes: {active_tapes}",
                f"Total Capacity: {total_size / (1024**3):.1f} GB",
                ""
            ])
            
            # Tape details
            report_lines.append("TAPE DETAILS:")
            for tape in tapes:
                archives = self.db_manager.get_tape_contents(tape['tape_id'])
                archive_count = len(archives)
                total_files = sum(a.get('file_count', 0) or 0 for a in archives)
                
                report_lines.extend([
                    f"  {tape['tape_label']} [{tape.get('tape_status', 'unknown')}]",
                    f"    Size: {(tape.get('total_size_bytes', 0) or 0) / (1024**3):.1f} GB",
                    f"    Archives: {archive_count}",
                    f"    Files: {total_files:,}",
                    f"    Device: {tape.get('tape_device', 'Unknown')}",
                    f"    Created: {tape.get('created_date', 'Unknown')}",
                    ""
                ])
            
            # Show report
            sg.popup_scrolled(
                '\n'.join(report_lines),
                title='Library Report',
                size=(70, 30)
            )
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            sg.popup_error(f"Failed to generate report: {e}")


def main():
    """Main function for testing tape browser."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Initialize components
        db_manager = DatabaseManager()
        recovery_manager = RecoveryManager(db_manager)
        
        # Create and run tape browser
        browser = TapeBrowser(db_manager, recovery_manager)
        browser.run_browser_interface()
        
    except Exception as e:
        sg.popup_error(f"Tape browser failed: {e}")
        logging.error(f"Tape browser error: {e}")


if __name__ == '__main__':
    main()

