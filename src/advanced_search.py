#!/usr/bin/env python3
"""
BackupUSSY Advanced Search
Enhanced search capabilities with filtering, regex, and specialized options.
"""

import os
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable, Union, Tuple
from pathlib import Path

try:
    import FreeSimpleGUI as sg
except ImportError:
    print("FreeSimpleGUI not installed. Please run: pip install FreeSimpleGUI")
    exit(1)

from version import ADVANCED_SEARCH_TITLE
from database_manager import DatabaseManager
from search_interface import SearchInterface

logger = logging.getLogger(__name__)

class AdvancedSearchManager:
    """Advanced search capabilities for archived files."""
    
    def __init__(self, database_manager):
        """Initialize advanced search manager.
        
        Args:
            database_manager: DatabaseManager instance
        """
        self.db_manager = database_manager
        self.search_history = []
        self.saved_searches = {}
        
        logger.info("Advanced search manager initialized")
    
    def regex_search(self, pattern: str, field: str = 'file_path', 
                    case_sensitive: bool = False, **filters) -> List[Dict[str, Any]]:
        """Search using regular expressions.
        
        Args:
            pattern: Regular expression pattern
            field: Field to search in ('file_path', 'archive_name', etc.)
            case_sensitive: Whether search is case sensitive
            **filters: Additional search filters
            
        Returns:
            List of matching file records
        """
        try:
            logger.info(f"Regex search: '{pattern}' in {field}")
            
            # Validate regex pattern
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                compiled_pattern = re.compile(pattern, flags)
            except re.error as e:
                logger.error(f"Invalid regex pattern: {e}")
                return []
            
            # Get all files matching other filters first
            base_query = "SELECT f.*, a.archive_name, a.source_folder, t.tape_label, t.tape_device " \
                        "FROM files f " \
                        "JOIN archives a ON f.archive_id = a.archive_id " \
                        "JOIN tapes t ON a.tape_id = t.tape_id"
            
            conditions = []
            params = []
            
            # Apply standard filters
            if filters.get('file_type'):
                conditions.append("f.file_type = ?")
                params.append(filters['file_type'])
            
            if filters.get('tape_id'):
                conditions.append("t.tape_id = ?")
                params.append(filters['tape_id'])
            
            if filters.get('date_from'):
                conditions.append("f.file_modified >= ?")
                params.append(filters['date_from'])
            
            if filters.get('date_to'):
                conditions.append("f.file_modified <= ?")
                params.append(filters['date_to'])
            
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            
            # Execute base query
            cursor = self.db_manager.conn.execute(base_query, params)
            all_results = cursor.fetchall()
            
            # Apply regex filter in Python
            filtered_results = []
            for row in all_results:
                row_dict = dict(row)
                field_value = row_dict.get(field, '')
                if field_value and compiled_pattern.search(str(field_value)):
                    filtered_results.append(row_dict)
            
            logger.info(f"Regex search found {len(filtered_results)} matches")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Regex search failed: {e}")
            return []
    
    def size_range_search(self, min_size: int = None, max_size: int = None, 
                         unit: str = 'bytes', **filters) -> List[Dict[str, Any]]:
        """Search files by size range.
        
        Args:
            min_size: Minimum file size
            max_size: Maximum file size
            unit: Size unit ('bytes', 'KB', 'MB', 'GB')
            **filters: Additional search filters
            
        Returns:
            List of matching file records
        """
        try:
            # Convert to bytes
            multipliers = {
                'bytes': 1,
                'KB': 1024,
                'MB': 1024 * 1024,
                'GB': 1024 * 1024 * 1024
            }
            
            multiplier = multipliers.get(unit, 1)
            min_bytes = min_size * multiplier if min_size is not None else None
            max_bytes = max_size * multiplier if max_size is not None else None
            
            logger.info(f"Size range search: {min_bytes}-{max_bytes} bytes")
            
            # Add size conditions to filters
            if min_bytes is not None:
                filters['min_size_bytes'] = min_bytes
            if max_bytes is not None:
                filters['max_size_bytes'] = max_bytes
            
            # Use database manager's search with size filters
            return self.db_manager.search_files(**filters)
            
        except Exception as e:
            logger.error(f"Size range search failed: {e}")
            return []
    
    def duplicate_file_search(self, criteria: str = 'name') -> List[Dict[str, Any]]:
        """Find duplicate files based on different criteria.
        
        Args:
            criteria: Duplicate detection criteria ('name', 'size', 'name_and_size')
            
        Returns:
            List of duplicate file groups
        """
        try:
            logger.info(f"Searching for duplicates by {criteria}")
            
            if criteria == 'name':
                query = """
                    SELECT f.file_path, f.file_size_bytes, f.file_modified,
                           a.archive_name, t.tape_label, COUNT(*) as duplicate_count,
                           GROUP_CONCAT(a.archive_id) as archive_ids
                    FROM files f
                    JOIN archives a ON f.archive_id = a.archive_id
                    JOIN tapes t ON a.tape_id = t.tape_id
                    GROUP BY f.file_path
                    HAVING COUNT(*) > 1
                    ORDER BY duplicate_count DESC
                """
            elif criteria == 'size':
                query = """
                    SELECT f.file_size_bytes, COUNT(*) as duplicate_count,
                           GROUP_CONCAT(f.file_path) as file_paths,
                           GROUP_CONCAT(a.archive_name) as archive_names
                    FROM files f
                    JOIN archives a ON f.archive_id = a.archive_id
                    GROUP BY f.file_size_bytes
                    HAVING COUNT(*) > 1 AND f.file_size_bytes > 0
                    ORDER BY duplicate_count DESC
                """
            else:  # name_and_size
                query = """
                    SELECT f.file_path, f.file_size_bytes, COUNT(*) as duplicate_count,
                           GROUP_CONCAT(a.archive_name) as archive_names,
                           GROUP_CONCAT(t.tape_label) as tape_labels
                    FROM files f
                    JOIN archives a ON f.archive_id = a.archive_id
                    JOIN tapes t ON a.tape_id = t.tape_id
                    GROUP BY f.file_path, f.file_size_bytes
                    HAVING COUNT(*) > 1
                    ORDER BY duplicate_count DESC
                """
            
            cursor = self.db_manager.conn.execute(query)
            results = [dict(row) for row in cursor.fetchall()]
            
            logger.info(f"Found {len(results)} duplicate groups")
            return results
            
        except Exception as e:
            logger.error(f"Duplicate search failed: {e}")
            return []
    
    def archive_content_search(self, query: str, archive_id: int = None) -> List[Dict[str, Any]]:
        """Search within specific archive contents.
        
        Args:
            query: Search query
            archive_id: Specific archive ID to search in
            
        Returns:
            List of matching files in the archive
        """
        try:
            logger.info(f"Archive content search: '{query}' in archive {archive_id}")
            
            base_query = """
                SELECT f.*, a.archive_name, a.source_folder, t.tape_label, t.tape_device
                FROM files f
                JOIN archives a ON f.archive_id = a.archive_id
                JOIN tapes t ON a.tape_id = t.tape_id
                WHERE f.file_path LIKE ?
            """
            
            params = [f"%{query}%"]
            
            if archive_id:
                base_query += " AND a.archive_id = ?"
                params.append(archive_id)
            
            cursor = self.db_manager.conn.execute(base_query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            logger.info(f"Found {len(results)} files in archive")
            return results
            
        except Exception as e:
            logger.error(f"Archive content search failed: {e}")
            return []
    
    def complex_query_search(self, conditions: List[Dict[str, Any]], 
                           operator: str = 'AND') -> List[Dict[str, Any]]:
        """Execute complex search with multiple conditions.
        
        Args:
            conditions: List of search conditions
            operator: Logical operator between conditions ('AND', 'OR')
            
        Returns:
            List of matching file records
        """
        try:
            logger.info(f"Complex query with {len(conditions)} conditions ({operator})")
            
            base_query = """
                SELECT f.*, a.archive_name, a.source_folder, a.archive_date,
                       t.tape_label, t.tape_device
                FROM files f
                JOIN archives a ON f.archive_id = a.archive_id
                JOIN tapes t ON a.tape_id = t.tape_id
            """
            
            where_clauses = []
            params = []
            
            for condition in conditions:
                field = condition.get('field')
                operator_type = condition.get('operator', '=')
                value = condition.get('value')
                
                if not field or value is None:
                    continue
                
                if operator_type == 'LIKE':
                    where_clauses.append(f"{field} LIKE ?")
                    params.append(f"%{value}%")
                elif operator_type == 'REGEX':
                    # Handle regex in Python after fetching results
                    continue
                elif operator_type in ['>', '<', '>=', '<=', '=', '!=']:
                    where_clauses.append(f"{field} {operator_type} ?")
                    params.append(value)
            
            if where_clauses:
                base_query += " WHERE " + f" {operator} ".join(where_clauses)
            
            cursor = self.db_manager.conn.execute(base_query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            # Apply regex conditions in Python
            for condition in conditions:
                if condition.get('operator') == 'REGEX':
                    field = condition.get('field')
                    pattern = condition.get('value')
                    try:
                        regex = re.compile(pattern, re.IGNORECASE)
                        results = [r for r in results if regex.search(str(r.get(field, '')))]
                    except re.error:
                        continue
            
            logger.info(f"Complex query returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Complex query search failed: {e}")
            return []
    
    def statistical_search(self) -> Dict[str, Any]:
        """Get statistical information about archived files.
        
        Returns:
            Dictionary with various statistics
        """
        try:
            stats = {}
            
            # Total files and size
            cursor = self.db_manager.conn.execute(
                "SELECT COUNT(*), SUM(file_size_bytes) FROM files"
            )
            total_files, total_size = cursor.fetchone()
            stats['total_files'] = total_files or 0
            stats['total_size_bytes'] = total_size or 0
            
            # File type distribution
            cursor = self.db_manager.conn.execute(
                "SELECT file_type, COUNT(*) FROM files GROUP BY file_type ORDER BY COUNT(*) DESC"
            )
            stats['file_types'] = dict(cursor.fetchall())
            
            # Largest files
            cursor = self.db_manager.conn.execute(
                "SELECT file_path, file_size_bytes FROM files ORDER BY file_size_bytes DESC LIMIT 10"
            )
            stats['largest_files'] = [dict(row) for row in cursor.fetchall()]
            
            # Archive statistics
            cursor = self.db_manager.conn.execute(
                "SELECT COUNT(*), AVG(file_count), SUM(archive_size_bytes) FROM archives"
            )
            archive_count, avg_files, total_archive_size = cursor.fetchone()
            stats['total_archives'] = archive_count or 0
            stats['avg_files_per_archive'] = avg_files or 0
            stats['total_archive_size_bytes'] = total_archive_size or 0
            
            # Tape statistics
            cursor = self.db_manager.conn.execute(
                "SELECT COUNT(*), SUM(total_size_bytes) FROM tapes"
            )
            tape_count, total_tape_size = cursor.fetchone()
            stats['total_tapes'] = tape_count or 0
            stats['total_tape_size_bytes'] = total_tape_size or 0
            
            # Recent activity
            cursor = self.db_manager.conn.execute(
                "SELECT COUNT(*) FROM archives WHERE archive_date >= datetime('now', '-30 days')"
            )
            stats['recent_archives'] = cursor.fetchone()[0] or 0
            
            logger.info("Generated archive statistics")
            return stats
            
        except Exception as e:
            logger.error(f"Statistical search failed: {e}")
            return {}
    
    def save_search(self, name: str, search_params: Dict[str, Any]):
        """Save search parameters for later use.
        
        Args:
            name: Name for the saved search
            search_params: Search parameters to save
        """
        try:
            self.saved_searches[name] = {
                'params': search_params,
                'created': datetime.now(),
                'last_used': None
            }
            logger.info(f"Saved search '{name}'")
        except Exception as e:
            logger.error(f"Failed to save search: {e}")
    
    def load_saved_search(self, name: str) -> Dict[str, Any]:
        """Load previously saved search parameters.
        
        Args:
            name: Name of the saved search
            
        Returns:
            Saved search parameters
        """
        try:
            if name in self.saved_searches:
                search_data = self.saved_searches[name]
                search_data['last_used'] = datetime.now()
                logger.info(f"Loaded saved search '{name}'")
                return search_data['params']
            return {}
        except Exception as e:
            logger.error(f"Failed to load saved search: {e}")
            return {}
    
    def add_to_search_history(self, search_params: Dict[str, Any]):
        """Add search to history.
        
        Args:
            search_params: Search parameters to add to history
        """
        try:
            history_entry = {
                'params': search_params,
                'timestamp': datetime.now(),
                'results_count': search_params.get('results_count', 0)
            }
            
            self.search_history.append(history_entry)
            
            # Keep only last 50 searches
            if len(self.search_history) > 50:
                self.search_history = self.search_history[-50:]
                
            logger.debug("Added search to history")
        except Exception as e:
            logger.error(f"Failed to add search to history: {e}")
    
    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions based on history and database content.
        
        Args:
            partial_query: Partial search query
            
        Returns:
            List of suggested completions
        """
        try:
            suggestions = set()
            
            # Get suggestions from file paths
            cursor = self.db_manager.conn.execute(
                "SELECT DISTINCT file_path FROM files WHERE file_path LIKE ? LIMIT 10",
                [f"%{partial_query}%"]
            )
            for row in cursor.fetchall():
                file_path = row[0]
                # Extract relevant parts of the path
                path_parts = file_path.split('/')
                for part in path_parts:
                    if partial_query.lower() in part.lower():
                        suggestions.add(part)
            
            # Get suggestions from file types
            cursor = self.db_manager.conn.execute(
                "SELECT DISTINCT file_type FROM files WHERE file_type LIKE ? LIMIT 5",
                [f"%{partial_query}%"]
            )
            suggestions.update(row[0] for row in cursor.fetchall())
            
            # Get suggestions from archive names
            cursor = self.db_manager.conn.execute(
                "SELECT DISTINCT archive_name FROM archives WHERE archive_name LIKE ? LIMIT 5",
                [f"%{partial_query}%"]
            )
            suggestions.update(row[0] for row in cursor.fetchall())
            
            return sorted(list(suggestions))[:10]
            
        except Exception as e:
            logger.error(f"Failed to get search suggestions: {e}")
            return []


class AdvancedSearchGUI:
    """GUI for advanced search features."""
    
    def __init__(self, database_manager, advanced_search_manager):
        """Initialize advanced search GUI.
        
        Args:
            database_manager: DatabaseManager instance
            advanced_search_manager: AdvancedSearchManager instance
        """
        self.db_manager = database_manager
        self.advanced_search = advanced_search_manager
        self.window = None
        
        logger.info("Advanced search GUI initialized")
    
    def create_advanced_search_window(self) -> sg.Window:
        """Create advanced search window.
        
        Returns:
            PySimpleGUI Window object
        """
        # Search type selection
        search_type_frame = [
            [sg.Text('Search Type:', font=('Arial', 10, 'bold'))],
            [sg.Radio('Text Search', 'SEARCH_TYPE', key='-TEXT_SEARCH-', default=True),
             sg.Radio('Regex Search', 'SEARCH_TYPE', key='-REGEX_SEARCH-'),
             sg.Radio('Size Range', 'SEARCH_TYPE', key='-SIZE_SEARCH-')],
            [sg.Radio('Duplicate Files', 'SEARCH_TYPE', key='-DUPLICATE_SEARCH-'),
             sg.Radio('Complex Query', 'SEARCH_TYPE', key='-COMPLEX_SEARCH-'),
             sg.Radio('Statistics', 'SEARCH_TYPE', key='-STATS_SEARCH-')]
        ]
        
        # Search parameters
        search_params_frame = [
            [sg.Text('Query:', size=(10, 1)), 
             sg.Input(key='-ADV_QUERY-', size=(40, 1)),
             sg.Button('Suggestions', key='-SUGGESTIONS-')],
            [sg.Text('Field:', size=(10, 1)),
             sg.Combo(['file_path', 'archive_name', 'file_type'], 
                     default_value='file_path', key='-SEARCH_FIELD-', size=(15, 1)),
             sg.Checkbox('Case Sensitive', key='-CASE_SENSITIVE-')]
        ]
        
        # Size search frame
        size_search_frame = [
            [sg.Text('Size Range:')],
            [sg.Text('Min:', size=(4, 1)), sg.Input(key='-MIN_SIZE-', size=(10, 1)),
             sg.Text('Max:', size=(4, 1)), sg.Input(key='-MAX_SIZE-', size=(10, 1)),
             sg.Combo(['bytes', 'KB', 'MB', 'GB'], default_value='MB', key='-SIZE_UNIT-')]
        ]
        
        # Duplicate search options
        duplicate_frame = [
            [sg.Text('Find Duplicates By:')],
            [sg.Radio('File Name', 'DUP_TYPE', key='-DUP_NAME-', default=True),
             sg.Radio('File Size', 'DUP_TYPE', key='-DUP_SIZE-'),
             sg.Radio('Name + Size', 'DUP_TYPE', key='-DUP_BOTH-')]
        ]
        
        # Standard filters
        filters_frame = [
            [sg.Text('Filters:', font=('Arial', 10, 'bold'))],
            [sg.Text('File Type:', size=(10, 1)),
             sg.Combo(['All Types', '.txt', '.jpg', '.png', '.pdf', '.doc', '.zip'], 
                     default_value='All Types', key='-ADV_FILE_TYPE-', size=(15, 1))],
            [sg.Text('Date From:', size=(10, 1)), sg.Input(key='-ADV_DATE_FROM-', size=(12, 1)),
             sg.CalendarButton('📅', target='-ADV_DATE_FROM-'),
             sg.Text('To:', size=(3, 1)), sg.Input(key='-ADV_DATE_TO-', size=(12, 1)),
             sg.CalendarButton('📅', target='-ADV_DATE_TO-')]
        ]
        
        # Saved searches
        saved_searches_frame = [
            [sg.Text('Saved Searches:', font=('Arial', 10, 'bold'))],
            [sg.Listbox(values=list(self.advanced_search.saved_searches.keys()),
                       key='-SAVED_SEARCHES-', size=(25, 4))],
            [sg.Button('Load', key='-LOAD_SEARCH-'), 
             sg.Button('Save Current', key='-SAVE_SEARCH-'),
             sg.Button('Delete', key='-DELETE_SEARCH-')]
        ]
        
        # Results display
        results_frame = [
            [sg.Text('Advanced Search Results:', font=('Arial', 10, 'bold'))],
            [sg.Table(
                values=[],
                headings=['File Path', 'Size', 'Type', 'Archive', 'Tape'],
                key='-ADV_RESULTS-',
                auto_size_columns=False,
                col_widths=[40, 12, 8, 25, 15],
                num_rows=12,
                alternating_row_color='lightblue',
                enable_events=True,
                select_mode=sg.TABLE_SELECT_MODE_EXTENDED
            )],
            [sg.Text('Results: 0 files', key='-ADV_RESULTS_COUNT-')]
        ]
        
        # Action buttons
        action_frame = [
            [sg.Button('Search', key='-ADV_SEARCH_BTN-', bind_return_key=True),
             sg.Button('Clear', key='-ADV_CLEAR-'),
             sg.Button('Export Results', key='-ADV_EXPORT-'),
             sg.Button('View Statistics', key='-VIEW_STATS-')]
        ]
        
        # Main layout with tabs
        tab1_layout = [
            [sg.Frame('Search Type', search_type_frame)],
            [sg.Frame('Search Parameters', search_params_frame)],
            [sg.Frame('Size Search', size_search_frame, visible=False, key='-SIZE_FRAME-')],
            [sg.Frame('Duplicate Search', duplicate_frame, visible=False, key='-DUP_FRAME-')],
            [sg.Frame('Filters', filters_frame)]
        ]
        
        tab2_layout = [
            [sg.Frame('Saved Searches', saved_searches_frame)]
        ]
        
        layout = [
            [sg.TabGroup([
                [sg.Tab('Search', tab1_layout),
                 sg.Tab('Saved', tab2_layout)]
            ])],
            [sg.Frame('Actions', action_frame)],
            [sg.Frame('Results', results_frame, expand_x=True, expand_y=True)],
            [sg.Button('Close', key='-ADV_CLOSE-')]
        ]
        
        self.window = sg.Window(
            ADVANCED_SEARCH_TITLE,
            layout,
            size=(900, 800),
            resizable=True,
            finalize=True
        )
        
        return self.window
    
    def run_advanced_search_interface(self):
        """Run the advanced search interface."""
        if not self.window:
            self.create_advanced_search_window()
        
        logger.info("Starting advanced search interface")
        
        while True:
            event, values = self.window.read()
            
            if event in (sg.WIN_CLOSED, '-ADV_CLOSE-'):
                break
            
            elif event in ['-TEXT_SEARCH-', '-REGEX_SEARCH-', '-SIZE_SEARCH-', 
                          '-DUPLICATE_SEARCH-', '-COMPLEX_SEARCH-', '-STATS_SEARCH-']:
                # Show/hide relevant frames based on search type
                self.window['-SIZE_FRAME-'].update(visible=values['-SIZE_SEARCH-'])
                self.window['-DUP_FRAME-'].update(visible=values['-DUPLICATE_SEARCH-'])
            
            elif event == '-ADV_SEARCH_BTN-':
                self._perform_advanced_search(values)
            
            elif event == '-ADV_CLEAR-':
                self._clear_advanced_search()
            
            elif event == '-SUGGESTIONS-':
                self._show_search_suggestions(values['-ADV_QUERY-'])
            
            elif event == '-SAVE_SEARCH-':
                self._save_current_search(values)
            
            elif event == '-LOAD_SEARCH-':
                self._load_saved_search(values)
            
            elif event == '-DELETE_SEARCH-':
                self._delete_saved_search(values)
            
            elif event == '-VIEW_STATS-':
                self._view_statistics()
            
            elif event == '-ADV_EXPORT-':
                self._export_results()
        
        self.window.close()
        logger.info("Advanced search interface closed")
    
    def _perform_advanced_search(self, values):
        """Perform the selected type of advanced search."""
        try:
            results = []
            
            if values['-TEXT_SEARCH-']:
                # Standard text search with filters
                query = values['-ADV_QUERY-']
                filters = self._get_filters(values)
                results = self.db_manager.search_files(query, **filters)
            
            elif values['-REGEX_SEARCH-']:
                # Regex search
                pattern = values['-ADV_QUERY-']
                field = values['-SEARCH_FIELD-']
                case_sensitive = values['-CASE_SENSITIVE-']
                filters = self._get_filters(values)
                results = self.advanced_search.regex_search(
                    pattern, field, case_sensitive, **filters
                )
            
            elif values['-SIZE_SEARCH-']:
                # Size range search
                min_size = values['-MIN_SIZE-']
                max_size = values['-MAX_SIZE-']
                unit = values['-SIZE_UNIT-']
                filters = self._get_filters(values)
                
                min_val = int(min_size) if min_size else None
                max_val = int(max_size) if max_size else None
                
                results = self.advanced_search.size_range_search(
                    min_val, max_val, unit, **filters
                )
            
            elif values['-DUPLICATE_SEARCH-']:
                # Duplicate file search
                if values['-DUP_NAME-']:
                    criteria = 'name'
                elif values['-DUP_SIZE-']:
                    criteria = 'size'
                else:
                    criteria = 'name_and_size'
                
                results = self.advanced_search.duplicate_file_search(criteria)
            
            elif values['-STATS_SEARCH-']:
                # Statistics view
                self._view_statistics()
                return
            
            # Display results
            self._display_advanced_results(results)
            
            # Add to search history
            search_params = {
                'query': values['-ADV_QUERY-'],
                'type': self._get_search_type(values),
                'filters': self._get_filters(values),
                'results_count': len(results)
            }
            self.advanced_search.add_to_search_history(search_params)
            
        except Exception as e:
            logger.error(f"Advanced search failed: {e}")
            sg.popup_error(f"Search failed: {e}")
    
    def _get_filters(self, values) -> Dict[str, Any]:
        """Extract filter values from form."""
        filters = {}
        
        if values['-ADV_FILE_TYPE-'] != 'All Types':
            filters['file_type'] = values['-ADV_FILE_TYPE-']
        
        if values['-ADV_DATE_FROM-']:
            try:
                filters['date_from'] = datetime.strptime(values['-ADV_DATE_FROM-'], '%Y-%m-%d')
            except ValueError:
                pass
        
        if values['-ADV_DATE_TO-']:
            try:
                filters['date_to'] = datetime.strptime(values['-ADV_DATE_TO-'], '%Y-%m-%d')
            except ValueError:
                pass
        
        return filters
    
    def _get_search_type(self, values) -> str:
        """Determine which search type is selected."""
        if values['-REGEX_SEARCH-']:
            return 'regex'
        elif values['-SIZE_SEARCH-']:
            return 'size'
        elif values['-DUPLICATE_SEARCH-']:
            return 'duplicate'
        elif values['-COMPLEX_SEARCH-']:
            return 'complex'
        elif values['-STATS_SEARCH-']:
            return 'statistics'
        else:
            return 'text'
    
    def _display_advanced_results(self, results):
        """Display search results in the table."""
        table_data = []
        
        for result in results:
            if 'duplicate_count' in result:
                # Special handling for duplicate results
                table_data.append([
                    result.get('file_path', 'Multiple files'),
                    f"{result.get('file_size_bytes', 0)} B",
                    'Duplicate',
                    result.get('archive_names', 'Multiple'),
                    f"{result.get('duplicate_count', 0)} copies"
                ])
            else:
                # Standard file results
                size_bytes = result.get('file_size_bytes', 0)
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                
                table_data.append([
                    result.get('file_path', ''),
                    size_str,
                    result.get('file_type', ''),
                    result.get('archive_name', ''),
                    result.get('tape_label', '')
                ])
        
        self.window['-ADV_RESULTS-'].update(values=table_data)
        self.window['-ADV_RESULTS_COUNT-'].update(f'Results: {len(results)} items')
    
    def _clear_advanced_search(self):
        """Clear all search fields and results."""
        self.window['-ADV_QUERY-'].update('')
        self.window['-SEARCH_FIELD-'].update('file_path')
        self.window['-CASE_SENSITIVE-'].update(False)
        self.window['-MIN_SIZE-'].update('')
        self.window['-MAX_SIZE-'].update('')
        self.window['-SIZE_UNIT-'].update('MB')
        self.window['-ADV_FILE_TYPE-'].update('All Types')
        self.window['-ADV_DATE_FROM-'].update('')
        self.window['-ADV_DATE_TO-'].update('')
        self.window['-ADV_RESULTS-'].update(values=[])
        self.window['-ADV_RESULTS_COUNT-'].update('Results: 0 items')
    
    def _show_search_suggestions(self, partial_query):
        """Show search suggestions popup."""
        if not partial_query:
            return
        
        suggestions = self.advanced_search.get_search_suggestions(partial_query)
        if suggestions:
            choice = sg.popup_get_text(
                f'Search suggestions for "{partial_query}":',
                default_text=suggestions[0] if suggestions else '',
                title='Search Suggestions'
            )
            if choice:
                self.window['-ADV_QUERY-'].update(choice)
    
    def _save_current_search(self, values):
        """Save current search parameters."""
        name = sg.popup_get_text('Enter name for saved search:')
        if name:
            search_params = {
                'query': values['-ADV_QUERY-'],
                'type': self._get_search_type(values),
                'filters': self._get_filters(values),
                'field': values['-SEARCH_FIELD-'],
                'case_sensitive': values['-CASE_SENSITIVE-']
            }
            self.advanced_search.save_search(name, search_params)
            
            # Update saved searches list
            self.window['-SAVED_SEARCHES-'].update(
                values=list(self.advanced_search.saved_searches.keys())
            )
            
            sg.popup(f'Search saved as "{name}"')
    
    def _load_saved_search(self, values):
        """Load a saved search."""
        selected = values['-SAVED_SEARCHES-']
        if selected:
            name = selected[0]
            params = self.advanced_search.load_saved_search(name)
            
            if params:
                self.window['-ADV_QUERY-'].update(params.get('query', ''))
                # Load other parameters as needed
                sg.popup(f'Loaded search "{name}"')
    
    def _delete_saved_search(self, values):
        """Delete a saved search."""
        selected = values['-SAVED_SEARCHES-']
        if selected:
            name = selected[0]
            if sg.popup_yes_no(f'Delete saved search "{name}"?') == 'Yes':
                if name in self.advanced_search.saved_searches:
                    del self.advanced_search.saved_searches[name]
                    self.window['-SAVED_SEARCHES-'].update(
                        values=list(self.advanced_search.saved_searches.keys())
                    )
                    sg.popup(f'Deleted search "{name}"')
    
    def _view_statistics(self):
        """Display archive statistics."""
        stats = self.advanced_search.statistical_search()
        
        if not stats:
            sg.popup('No statistics available')
            return
        
        # Format statistics for display
        stats_text = []
        stats_text.append(f"Total Files: {stats.get('total_files', 0):,}")
        stats_text.append(f"Total Size: {stats.get('total_size_bytes', 0) / (1024**3):.2f} GB")
        stats_text.append(f"Total Archives: {stats.get('total_archives', 0):,}")
        stats_text.append(f"Total Tapes: {stats.get('total_tapes', 0):,}")
        stats_text.append(f"Recent Archives (30 days): {stats.get('recent_archives', 0):,}")
        stats_text.append("")
        
        stats_text.append("File Types:")
        for file_type, count in list(stats.get('file_types', {}).items())[:10]:
            stats_text.append(f"  {file_type}: {count:,} files")
        
        stats_text.append("")
        stats_text.append("Largest Files:")
        for file_info in stats.get('largest_files', [])[:5]:
            size_mb = file_info['file_size_bytes'] / (1024 * 1024)
            stats_text.append(f"  {file_info['file_path']}: {size_mb:.1f} MB")
        
        # Show statistics in popup
        sg.popup_scrolled(
            '\n'.join(stats_text),
            title='Archive Statistics',
            size=(60, 25)
        )
    
    def _export_results(self):
        """Export current search results."""
        # This would integrate with the main search interface export functionality
        sg.popup('Export functionality would be integrated with main search interface')


def main():
    """Main function for testing advanced search."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Initialize components
        db_manager = DatabaseManager()
        advanced_search = AdvancedSearchManager(db_manager)
        
        # Create and run advanced search GUI
        gui = AdvancedSearchGUI(db_manager, advanced_search)
        gui.run_advanced_search_interface()
        
    except Exception as e:
        sg.popup_error(f"Advanced search failed: {e}")
        logging.error(f"Advanced search error: {e}")


if __name__ == '__main__':
    main()

