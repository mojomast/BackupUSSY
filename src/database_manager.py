#!/usr/bin/env python3
"""
Database Manager - SQLite operations for tape and file indexing.
Phase 2.1.1 - Core database functionality for LTO Tape Archive Tool.
"""

import sqlite3
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database for tape and file indexing."""
    
    def __init__(self, db_path: str = "../data/tape_index.db"):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        # Resolve relative path from src directory
        if db_path.startswith("../"):
            db_path = Path(__file__).parent.parent / db_path[3:]
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize_database()
        logger.info(f"Database manager initialized: {self.db_path}")
    
    def _initialize_database(self):
        """Create database tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create tapes table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tapes (
                        tape_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tape_label VARCHAR(50) UNIQUE,
                        tape_device VARCHAR(20),
                        created_date DATETIME,
                        last_written DATETIME,
                        total_size_bytes BIGINT DEFAULT 0,
                        compression_used BOOLEAN DEFAULT 0,
                        tape_status VARCHAR(20) DEFAULT 'active',
                        notes TEXT
                    )
                """)
                
                # Create archives table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS archives (
                        archive_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tape_id INTEGER,
                        archive_name VARCHAR(100),
                        source_folder VARCHAR(500),
                        archive_date DATETIME,
                        archive_size_bytes BIGINT,
                        file_count INTEGER,
                        checksum VARCHAR(64),
                        compression_used BOOLEAN,
                        archive_position INTEGER,
                        FOREIGN KEY (tape_id) REFERENCES tapes(tape_id)
                    )
                """)
                
                # Create files table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS files (
                        file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        archive_id INTEGER,
                        file_path VARCHAR(1000),
                        file_size_bytes BIGINT,
                        file_modified DATETIME,
                        file_type VARCHAR(10),
                        file_checksum VARCHAR(64),
                        FOREIGN KEY (archive_id) REFERENCES archives(archive_id)
                    )
                """)
                
                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_path ON files(file_path)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_archives_name ON archives(archive_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tapes_label ON tapes(tape_label)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_archives_date ON archives(archive_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_modified ON files(file_modified)")
                
                conn.commit()
                logger.info("Database tables and indexes created successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def add_tape(self, tape_label: str, device: str, notes: Optional[str] = None) -> int:
        """Add a new tape to the database.
        
        Args:
            tape_label: User-assigned label for the tape
            device: Tape device used (e.g., \\.\\Tape0)
            notes: Optional notes about the tape
            
        Returns:
            tape_id of the newly created tape
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                now = datetime.now()
                cursor.execute("""
                    INSERT INTO tapes (tape_label, tape_device, created_date, last_written, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (tape_label, device, now, now, notes))
                
                tape_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Added tape: {tape_label} (ID: {tape_id})")
                return tape_id
                
        except sqlite3.IntegrityError:
            logger.error(f"Tape label '{tape_label}' already exists")
            raise ValueError(f"Tape label '{tape_label}' already exists")
        except sqlite3.Error as e:
            logger.error(f"Failed to add tape: {e}")
            raise
    
    def add_archive(self, tape_id: int, archive_name: str, source_folder: str,
                   archive_size_bytes: int, file_count: int, checksum: str,
                   compression_used: bool = False, archive_position: int = 1) -> int:
        """Add a new archive to the database.
        
        Args:
            tape_id: ID of the tape containing this archive
            archive_name: Name of the archive file
            source_folder: Original folder path that was archived
            archive_size_bytes: Size of the archive in bytes
            file_count: Number of files in the archive
            checksum: SHA256 checksum of the archive
            compression_used: Whether compression was used
            archive_position: Position on tape (for multi-archive tapes)
            
        Returns:
            archive_id of the newly created archive
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verify tape exists
                cursor.execute("SELECT tape_id FROM tapes WHERE tape_id = ?", (tape_id,))
                if not cursor.fetchone():
                    raise ValueError(f"Tape ID {tape_id} does not exist")
                
                now = datetime.now()
                cursor.execute("""
                    INSERT INTO archives (tape_id, archive_name, source_folder, archive_date,
                                        archive_size_bytes, file_count, checksum, compression_used, archive_position)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (tape_id, archive_name, source_folder, now, archive_size_bytes,
                      file_count, checksum, compression_used, archive_position))
                
                archive_id = cursor.lastrowid
                
                # Update tape's last_written and total_size
                cursor.execute("""
                    UPDATE tapes 
                    SET last_written = ?, total_size_bytes = total_size_bytes + ?
                    WHERE tape_id = ?
                """, (now, archive_size_bytes, tape_id))
                
                conn.commit()
                
                logger.info(f"Added archive: {archive_name} (ID: {archive_id}) to tape {tape_id}")
                return archive_id
                
        except sqlite3.Error as e:
            logger.error(f"Failed to add archive: {e}")
            raise
    
    def add_files(self, archive_id: int, file_list: List[Dict[str, Any]]):
        """Add files to an archive in the database.
        
        Args:
            archive_id: ID of the archive containing these files
            file_list: List of file dictionaries with keys:
                      - file_path: relative path in archive
                      - file_size_bytes: file size
                      - file_modified: modification datetime
                      - file_type: file extension
                      - file_checksum: optional file checksum
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verify archive exists
                cursor.execute("SELECT archive_id FROM archives WHERE archive_id = ?", (archive_id,))
                if not cursor.fetchone():
                    raise ValueError(f"Archive ID {archive_id} does not exist")
                
                # Prepare file data for bulk insert
                file_data = []
                for file_info in file_list:
                    file_data.append((
                        archive_id,
                        file_info.get('file_path', ''),
                        file_info.get('file_size_bytes', 0),
                        file_info.get('file_modified'),
                        file_info.get('file_type', ''),
                        file_info.get('file_checksum')
                    ))
                
                cursor.executemany("""
                    INSERT INTO files (archive_id, file_path, file_size_bytes, file_modified, file_type, file_checksum)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, file_data)
                
                conn.commit()
                
                logger.info(f"Added {len(file_list)} files to archive {archive_id}")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to add files: {e}")
            raise
    
    def search_files(self, query: str, file_type: Optional[str] = None, 
                    tape_id: Optional[int] = None, date_from: Optional[datetime] = None,
                    date_to: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Search for files across all archives.
        
        Args:
            query: Search term for file paths (supports wildcards with %)
            file_type: Optional file extension filter (e.g., '.jpg')
            tape_id: Optional tape ID to limit search
            date_from: Optional start date filter
            date_to: Optional end date filter
            
        Returns:
            List of file records with archive and tape information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable column access by name
                cursor = conn.cursor()
                
                # Build dynamic query
                sql = """
                    SELECT f.file_id, f.file_path, f.file_size_bytes, f.file_modified, f.file_type,
                           a.archive_id, a.archive_name, a.source_folder, a.archive_date,
                           t.tape_id, t.tape_label, t.tape_device
                    FROM files f
                    JOIN archives a ON f.archive_id = a.archive_id
                    JOIN tapes t ON a.tape_id = t.tape_id
                    WHERE f.file_path LIKE ?
                """
                
                params = [f"%{query}%"]
                
                if file_type:
                    sql += " AND f.file_type = ?"
                    params.append(file_type)
                
                if tape_id:
                    sql += " AND t.tape_id = ?"
                    params.append(tape_id)
                
                if date_from:
                    sql += " AND f.file_modified >= ?"
                    params.append(date_from)
                
                if date_to:
                    sql += " AND f.file_modified <= ?"
                    params.append(date_to)
                
                sql += " ORDER BY f.file_path"
                
                cursor.execute(sql, params)
                results = [dict(row) for row in cursor.fetchall()]
                
                logger.info(f"Found {len(results)} files matching query: '{query}'")
                return results
                
        except sqlite3.Error as e:
            logger.error(f"Failed to search files: {e}")
            raise
    
    def get_tape_contents(self, tape_id: int) -> Dict[str, Any]:
        """Get all contents of a specific tape.
        
        Args:
            tape_id: ID of the tape
            
        Returns:
            Dictionary with tape info and list of archives
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get tape information
                cursor.execute("SELECT * FROM tapes WHERE tape_id = ?", (tape_id,))
                tape_info = cursor.fetchone()
                
                if not tape_info:
                    raise ValueError(f"Tape ID {tape_id} not found")
                
                # Get archives on this tape
                cursor.execute("""
                    SELECT a.*, COUNT(f.file_id) as file_count_actual
                    FROM archives a
                    LEFT JOIN files f ON a.archive_id = f.archive_id
                    WHERE a.tape_id = ?
                    GROUP BY a.archive_id
                    ORDER BY a.archive_position, a.archive_date
                """, (tape_id,))
                
                archives = [dict(row) for row in cursor.fetchall()]
                
                result = {
                    'tape_info': dict(tape_info),
                    'archives': archives,
                    'total_archives': len(archives),
                    'total_files': sum(archive['file_count_actual'] for archive in archives)
                }
                
                logger.info(f"Retrieved contents for tape {tape_id}: {len(archives)} archives")
                return result
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get tape contents: {e}")
            raise
    
    def get_archive_details(self, archive_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific archive.
        
        Args:
            archive_id: ID of the archive
            
        Returns:
            Dictionary with archive info and file list
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get archive information with tape details
                cursor.execute("""
                    SELECT a.*, t.tape_label, t.tape_device, t.tape_status
                    FROM archives a
                    JOIN tapes t ON a.tape_id = t.tape_id
                    WHERE a.archive_id = ?
                """, (archive_id,))
                
                archive_info = cursor.fetchone()
                
                if not archive_info:
                    raise ValueError(f"Archive ID {archive_id} not found")
                
                # Get files in this archive
                cursor.execute("""
                    SELECT * FROM files 
                    WHERE archive_id = ? 
                    ORDER BY file_path
                """, (archive_id,))
                
                files = [dict(row) for row in cursor.fetchall()]
                
                result = {
                    'archive_info': dict(archive_info),
                    'files': files,
                    'file_count': len(files)
                }
                
                logger.info(f"Retrieved details for archive {archive_id}: {len(files)} files")
                return result
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get archive details: {e}")
            raise
    
    def update_tape_status(self, tape_id: int, status: str, notes: Optional[str] = None):
        """Update tape status and notes.
        
        Args:
            tape_id: ID of the tape
            status: New status (active, full, damaged, retired, etc.)
            notes: Optional additional notes
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if notes is not None:
                    cursor.execute("""
                        UPDATE tapes 
                        SET tape_status = ?, notes = ?
                        WHERE tape_id = ?
                    """, (status, notes, tape_id))
                else:
                    cursor.execute("""
                        UPDATE tapes 
                        SET tape_status = ?
                        WHERE tape_id = ?
                    """, (status, tape_id))
                
                if cursor.rowcount == 0:
                    raise ValueError(f"Tape ID {tape_id} not found")
                
                conn.commit()
                
                logger.info(f"Updated tape {tape_id} status to: {status}")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to update tape status: {e}")
            raise
    
    def get_all_tapes(self) -> List[Dict[str, Any]]:
        """Get list of all tapes in the database.
        
        Returns:
            List of tape records with summary statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT t.*, 
                           COUNT(DISTINCT a.archive_id) as archive_count,
                           COUNT(f.file_id) as total_files
                    FROM tapes t
                    LEFT JOIN archives a ON t.tape_id = a.tape_id
                    LEFT JOIN files f ON a.archive_id = f.archive_id
                    GROUP BY t.tape_id
                    ORDER BY t.created_date DESC
                """)
                
                tapes = [dict(row) for row in cursor.fetchall()]
                
                logger.info(f"Retrieved {len(tapes)} tapes from database")
                return tapes
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get tape list: {e}")
            raise
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics.
        
        Returns:
            Dictionary with count statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                cursor.execute("SELECT COUNT(*) FROM tapes")
                stats['total_tapes'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM archives")
                stats['total_archives'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM files")
                stats['total_files'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT SUM(total_size_bytes) FROM tapes")
                result = cursor.fetchone()[0]
                stats['total_data_bytes'] = result if result else 0
                
                cursor.execute("SELECT COUNT(*) FROM tapes WHERE tape_status = 'active'")
                stats['active_tapes'] = cursor.fetchone()[0]
                
                return stats
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get database stats: {e}")
            raise
    
    def find_tape_by_label(self, tape_label: str) -> Optional[Dict[str, Any]]:
        """Find a tape by its label.
        
        Args:
            tape_label: Label to search for
            
        Returns:
            Tape record or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM tapes WHERE tape_label = ?", (tape_label,))
                result = cursor.fetchone()
                
                return dict(result) if result else None
                
        except sqlite3.Error as e:
            logger.error(f"Failed to find tape by label: {e}")
            raise
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """Create a backup of the database.
        
        Args:
            backup_path: Optional path for backup file
            
        Returns:
            Path to the backup file
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db_path.parent / "backups" / f"tape_index_backup_{timestamp}.db"
        
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Use SQLite backup API for safe backup
            with sqlite3.connect(self.db_path) as source:
                with sqlite3.connect(backup_path) as target:
                    source.backup(target)
            
            logger.info(f"Database backed up to: {backup_path}")
            return str(backup_path)
            
        except sqlite3.Error as e:
            logger.error(f"Failed to backup database: {e}")
            raise
    
    def export_inventory_csv(self, output_path: str) -> bool:
        """Export complete tape inventory to CSV format."""
        try:
            import csv
            from pathlib import Path
            
            output_dir = Path(output_path).parent / f"{Path(output_path).stem}_inventory"
            output_dir.mkdir(exist_ok=True)
            
            # Export tapes
            tapes = self.get_all_tapes()
            tapes_path = output_dir / 'tapes.csv'
            with open(tapes_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Tape ID', 'Label', 'Device', 'Status', 'Size (Bytes)', 'Created Date', 'Notes'])
                for tape in tapes:
                    writer.writerow([
                        tape['tape_id'],
                        tape['tape_label'],
                        tape.get('tape_device', ''),
                        tape.get('tape_status', 'unknown'),
                        tape.get('total_size_bytes', 0) or 0,
                        tape.get('created_date', ''),
                        tape.get('notes', '')
                    ])
            
            # Export archives
            archives = self.get_all_archives()
            archives_path = output_dir / 'archives.csv'
            with open(archives_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Archive ID', 'Tape ID', 'Archive Name', 'Source Folder',
                    'Archive Date', 'Size (Bytes)', 'File Count', 'Checksum'
                ])
                for archive in archives:
                    writer.writerow([
                        archive['archive_id'],
                        archive['tape_id'],
                        archive['archive_name'],
                        archive['source_folder'],
                        archive['archive_date'],
                        archive.get('archive_size_bytes', 0) or 0,
                        archive.get('file_count', 0) or 0,
                        archive.get('checksum', '')
                    ])
            
            # Export file index (summary by archive)
            files_summary_path = output_dir / 'files_summary.csv'
            with open(files_summary_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Archive ID', 'Archive Name', 'Total Files', 'Total Size (Bytes)', 'File Types'])
                
                for archive in archives:
                    files = self.get_archive_files(archive['archive_id'])
                    total_size = sum(f.get('file_size_bytes', 0) or 0 for f in files)
                    
                    # Count file types
                    file_types = {}
                    for file_info in files:
                        file_type = file_info.get('file_type', 'unknown')
                        file_types[file_type] = file_types.get(file_type, 0) + 1
                    
                    file_types_str = '; '.join([f"{k}:{v}" for k, v in file_types.items()])
                    
                    writer.writerow([
                        archive['archive_id'],
                        archive['archive_name'],
                        len(files),
                        total_size,
                        file_types_str
                    ])
            
            logger.info(f"Inventory exported to CSV in directory: {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export inventory to CSV: {e}")
            return False
    
    def export_inventory_json(self, output_path: str) -> bool:
        """Export complete tape inventory to JSON format."""
        try:
            import json
            
            inventory = {
                'export_date': datetime.now().isoformat(),
                'version': '2.0',
                'tapes': [],
                'archives': [],
                'statistics': self.get_library_statistics()
            }
            
            # Export tapes with their archives
            tapes = self.get_all_tapes()
            for tape in tapes:
                tape_data = dict(tape)
                
                # Get archives for this tape
                archives = self.get_tape_contents(tape['tape_id'])
                tape_archives = []
                
                for archive in archives:
                    archive_data = dict(archive)
                    
                    # Get files for this archive (sample for large archives)
                    files = self.get_archive_files(archive['archive_id'])
                    if len(files) > 1000:  # Limit file details for large archives
                        archive_data['files'] = files[:1000]  # First 1000 files
                        archive_data['files_truncated'] = True
                        archive_data['total_files'] = len(files)
                    else:
                        archive_data['files'] = files
                        archive_data['files_truncated'] = False
                    
                    tape_archives.append(archive_data)
                
                tape_data['archives'] = tape_archives
                inventory['tapes'].append(tape_data)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(inventory, f, indent=2, default=str, ensure_ascii=False)
            
            logger.info(f"Inventory exported to JSON: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export inventory to JSON: {e}")
            return False
    
    def import_inventory_csv(self, import_dir: str) -> int:
        """Import tape inventory from CSV directory."""
        try:
            import csv
            from pathlib import Path
            
            import_path = Path(import_dir)
            if import_path.is_file() and import_path.suffix == '.csv':
                # Single CSV file - assume it's tapes
                return self._import_tapes_csv(import_path)
            
            records_imported = 0
            
            # Import tapes first
            tapes_file = import_path / 'tapes.csv'
            if tapes_file.exists():
                records_imported += self._import_tapes_csv(tapes_file)
            
            # Import archives
            archives_file = import_path / 'archives.csv'
            if archives_file.exists():
                records_imported += self._import_archives_csv(archives_file)
            
            logger.info(f"Imported {records_imported} records from CSV")
            return records_imported
            
        except Exception as e:
            logger.error(f"Failed to import from CSV: {e}")
            return 0
    
    def _import_tapes_csv(self, csv_path) -> int:
        """Import tapes from CSV file."""
        import csv
        imported = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Check if tape already exists
                    existing = self.find_tape_by_label(row['Label'])
                    if existing:
                        logger.warning(f"Tape {row['Label']} already exists, skipping")
                        continue
                    
                    self.add_tape(
                        tape_label=row['Label'],
                        device=row.get('Device', ''),
                        notes=row.get('Notes', ''),
                        tape_status=row.get('Status', 'active')
                    )
                    imported += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to import tape {row.get('Label', 'unknown')}: {e}")
                    continue
        
        return imported
    
    def _import_archives_csv(self, csv_path) -> int:
        """Import archives from CSV file."""
        import csv
        imported = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Find the tape by ID or create mapping
                    tape_id = int(row['Tape ID'])
                    
                    # Check if archive already exists
                    existing = self.find_archive_by_name(row['Archive Name'])
                    if existing:
                        logger.warning(f"Archive {row['Archive Name']} already exists, skipping")
                        continue
                    
                    self.add_archive(
                        tape_id=tape_id,
                        archive_name=row['Archive Name'],
                        source_folder=row['Source Folder'],
                        archive_size_bytes=int(row.get('Size (Bytes)', 0)),
                        file_count=int(row.get('File Count', 0)),
                        checksum=row.get('Checksum', None),
                        compression_used=False  # Default value
                    )
                    imported += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to import archive {row.get('Archive Name', 'unknown')}: {e}")
                    continue
        
        return imported
    
    def import_inventory_json(self, json_path: str) -> int:
        """Import tape inventory from JSON file."""
        try:
            import json
            
            with open(json_path, 'r', encoding='utf-8') as f:
                inventory = json.load(f)
            
            records_imported = 0
            tape_id_mapping = {}  # Map old IDs to new IDs
            
            # Import tapes
            for tape_data in inventory.get('tapes', []):
                try:
                    # Check if tape already exists
                    existing = self.find_tape_by_label(tape_data['tape_label'])
                    if existing:
                        tape_id_mapping[tape_data['tape_id']] = existing['tape_id']
                        logger.warning(f"Tape {tape_data['tape_label']} already exists, using existing")
                        continue
                    
                    new_tape_id = self.add_tape(
                        tape_label=tape_data['tape_label'],
                        device=tape_data.get('tape_device', ''),
                        notes=tape_data.get('notes', ''),
                        tape_status=tape_data.get('tape_status', 'active')
                    )
                    
                    tape_id_mapping[tape_data['tape_id']] = new_tape_id
                    records_imported += 1
                    
                    # Import archives for this tape
                    for archive_data in tape_data.get('archives', []):
                        try:
                            # Check if archive already exists
                            existing_archive = self.find_archive_by_name(archive_data['archive_name'])
                            if existing_archive:
                                logger.warning(f"Archive {archive_data['archive_name']} already exists, skipping")
                                continue
                            
                            archive_id = self.add_archive(
                                tape_id=new_tape_id,
                                archive_name=archive_data['archive_name'],
                                source_folder=archive_data['source_folder'],
                                archive_size_bytes=archive_data.get('archive_size_bytes', 0),
                                file_count=archive_data.get('file_count', 0),
                                checksum=archive_data.get('checksum'),
                                compression_used=archive_data.get('compression_used', False)
                            )
                            
                            records_imported += 1
                            
                            # Import files if available and not truncated
                            if archive_data.get('files') and not archive_data.get('files_truncated', False):
                                files_data = archive_data['files']
                                if files_data:
                                    self.add_files(archive_id, files_data)
                                    records_imported += len(files_data)
                            
                        except Exception as e:
                            logger.warning(f"Failed to import archive {archive_data.get('archive_name', 'unknown')}: {e}")
                            continue
                    
                except Exception as e:
                    logger.warning(f"Failed to import tape {tape_data.get('tape_label', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Imported {records_imported} records from JSON")
            return records_imported
            
        except Exception as e:
            logger.error(f"Failed to import from JSON: {e}")
            return 0
    
    def get_all_archives(self) -> List[Dict]:
        """Get all archives from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT a.*, t.tape_label
                    FROM archives a
                    JOIN tapes t ON a.tape_id = t.tape_id
                    ORDER BY a.archive_date DESC
                """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get all archives: {e}")
            return []
    
    def get_tapes_by_device(self, device: str) -> List[Dict]:
        """Get all tapes for a specific device."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM tapes 
                    WHERE tape_device = ?
                    ORDER BY created_date DESC
                """, (device,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get tapes by device: {e}")
            return []
    
    def update_tape_write_completion(self, tape_id: int, bytes_written: int) -> bool:
        """Update tape with completion information after successful write."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update last written time and add to total size
                cursor.execute("""
                    UPDATE tapes 
                    SET last_written = ?,
                        total_size_bytes = COALESCE(total_size_bytes, 0) + ?
                    WHERE tape_id = ?
                """, (datetime.now().isoformat(), bytes_written, tape_id))
                
                conn.commit()
                logger.info(f"Updated tape {tape_id} with {bytes_written} bytes written")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to update tape write completion: {e}")
            return False
    
    def update_tape(self, tape_id: int, **kwargs) -> bool:
        """Update tape with new information."""
        try:
            if not kwargs:
                return True
                
            # Build dynamic update query
            valid_fields = ['tape_label', 'tape_device', 'tape_status', 'notes']
            update_fields = []
            values = []
            
            for field, value in kwargs.items():
                if field in valid_fields:
                    update_fields.append(f"{field} = ?")
                    values.append(value)
            
            if not update_fields:
                return True
            
            values.append(tape_id)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = f"UPDATE tapes SET {', '.join(update_fields)} WHERE tape_id = ?"
                cursor.execute(query, values)
                
                conn.commit()
                logger.info(f"Updated tape {tape_id}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to update tape: {e}")
            return False
    
    def delete_tape(self, tape_id: int) -> bool:
        """Delete a tape and all associated archives and files."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete files first (via cascade from archives)
                cursor.execute("SELECT archive_id FROM archives WHERE tape_id = ?", (tape_id,))
                archive_ids = [row[0] for row in cursor.fetchall()]
                
                for archive_id in archive_ids:
                    cursor.execute("DELETE FROM files WHERE archive_id = ?", (archive_id,))
                
                # Delete archives
                cursor.execute("DELETE FROM archives WHERE tape_id = ?", (tape_id,))
                
                # Delete tape
                cursor.execute("DELETE FROM tapes WHERE tape_id = ?", (tape_id,))
                
                conn.commit()
                logger.info(f"Deleted tape {tape_id} and all associated data")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to delete tape: {e}")
            return False

