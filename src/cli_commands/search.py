#!/usr/bin/env python3
"""
Search Command

Handles search operations across archives.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List

from .base import BaseCommand, BackupussyError, ValidationError

logger = logging.getLogger(__name__)

class SearchCommand(BaseCommand):
    """Handle search command and subcommands."""
    
    def __init__(self, managers): 
        super().__init__(managers) 
        # self.db_manager is now correctly inherited from BaseCommand
        self.name = "search"
        self.description = "Search for files, archives, or tapes."

    def execute(self, args):
        """Execute the search command."""
        self.logger.info(f"Executing search command with args: {args}")
        
        query = args.query if args.query else args.name # Use positional query if provided
        if not query and not args.name:
            # If neither positional query nor --name is provided, search for all of specified entity type
            self.logger.info(f"No specific query provided. Searching all entries for entity type: {args.entity}")
            query = "" # Empty query to fetch all, filters will apply
        elif not query and args.name:
            query = args.name # Use --name if positional query is not provided

        # Determine search type (file, archive, tape) from --entity argument
        search_type = args.entity

        filters = self._build_filters(args, query, search_type) # Pass search_type to _build_filters
        self.logger.debug(f"Search type: {search_type}, Query: '{query}', Filters: {filters}")

        results = self.db_manager.search(query, search_type, filters)

        if not results:
            print(f"No {search_type}s found matching your query.")
            return 0

        if search_type == 'file':
            self._display_file_results(results)
        elif search_type == 'archive':
            self._display_archive_results(results)
        elif search_type == 'tape':
            self._display_tape_results(results)
        
        return 0

    def _build_filters(self, args, query: str, search_type: str) -> Dict[str, Any]:
        """Build a dictionary of filters from command line arguments."""
        filters = {}
        if query: # The main query string for filename, archive name, or tape label
            filters['query'] = query

        # File-specific filters
        if search_type == 'file':
            if args.type: # This is for file extension filter like 'pdf', 'txt'
                filters['file_type'] = args.type

        if args.tape:
            tape = self.db_manager.find_tape_by_label(args.tape)
            if not tape:
                raise ValidationError(f"Tape '{args.tape}' not found.")
            filters['tape_id'] = tape['tape_id']

        if args.modified_after:
            try:
                filters['date_from'] = datetime.strptime(args.modified_after, '%Y-%m-%d')
            except ValueError:
                raise ValidationError("Invalid 'after' date format. Please use YYYY-MM-DD.")

        if args.modified_before:
            try:
                filters['date_to'] = datetime.strptime(args.modified_before, '%Y-%m-%d')
            except ValueError:
                raise ValidationError("Invalid 'before' date format. Please use YYYY-MM-DD.")
        
        return filters

    def _display_file_results(self, results: List[Dict[str, Any]]):
        print(f"Found {len(results)} file(s):")
        print(f"{"File Path":<60} {"Size":>12} {"Modified Date":<20} {"Archive":<30} {"Tape":<20}")
        print("-" * 150)
        for r in results:
            size_str = self._format_size(r.get('file_size_bytes', 0))
            date_str = self._format_date(r.get('file_modified'))
            print(f"{r.get('file_path', ''):<60} {size_str:>12} {date_str:<20} {r.get('archive_name', ''):<30} {r.get('tape_label', ''):<20}")

    def _display_archive_results(self, results: List[Dict[str, Any]]):
        print(f"Found {len(results)} archive(s):")
        print(f"{"Archive Name":<40} {"Date":<20} {"Size":>12} {"Files":>8} {"Tape":<20}")
        print("-" * 110)
        for r in results:
            size_str = self._format_size(r.get('archive_size_bytes', 0))
            date_str = self._format_date(r.get('archive_date'))
            print(f"{r.get('archive_name', ''):<40} {date_str:<20} {size_str:>12} {r.get('file_count', 0):>8} {r.get('tape_label', ''):<20}")

    def _display_tape_results(self, results: List[Dict[str, Any]]):
        print(f"Found {len(results)} tape(s):")
        print(f"{"Tape Label":<30} {"Status":<15} {"Last Written":<20} {"Size":>12} {"Notes":<40}")
        print("-" * 125)
        for r in results:
            size_str = self._format_size(r.get('total_size_bytes', 0))
            date_str = self._format_date(r.get('last_written'))
            print(f"{r.get('tape_label', ''):<30} {r.get('tape_status', ''):<15} {date_str:<20} {size_str:>12} {r.get('notes', ''):<40}")

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.2f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/1024**2:.2f} MB"
        else:
            return f"{size_bytes/1024**3:.2f} GB"

    def _format_date(self, date_input) -> str:
        if not date_input:
            return ""
        try:
            if isinstance(date_input, str):
                # Handle ISO format with or without microseconds
                if '.' in date_input:
                    date_obj = datetime.fromisoformat(date_input.split('.')[0])
                else:
                    date_obj = datetime.fromisoformat(date_input)
            else:
                date_obj = date_input
            return date_obj.strftime('%Y-%m-%d %H:%M')
        except (ValueError, TypeError):
            return str(date_input)
