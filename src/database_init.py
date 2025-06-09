#!/usr/bin/env python3
"""
Database Initialization - Handles first-time setup, migrations, and maintenance.
Phase 2.1.3 - Database initialization for LTO Tape Archive Tool.
"""

import os
import sqlite3
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Handles database initialization, migrations, and maintenance."""
    
    # Database schema version for migrations
    CURRENT_SCHEMA_VERSION = 1
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database initializer.
        
        Args:
            db_path: Optional custom database path
        """
        self.db_path = db_path
        
    def setup_database(self, force_recreate: bool = False) -> DatabaseManager:
        """Set up the database with initial configuration.
        
        Args:
            force_recreate: If True, recreate database even if it exists
            
        Returns:
            Configured DatabaseManager instance
        """
        try:
            # Create database manager
            db_manager = DatabaseManager(self.db_path) if self.db_path else DatabaseManager()
            
            # Check if database exists and has data
            if force_recreate or self._should_initialize_database(db_manager):
                logger.info("Initializing database with sample data and configuration...")
                self._initialize_sample_data(db_manager)
            
            # Set up database metadata
            self._setup_metadata(db_manager)
            
            # Create backup
            backup_path = db_manager.backup_database()
            logger.info(f"Initial database backup created: {backup_path}")
            
            logger.info("Database setup completed successfully")
            return db_manager
            
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            raise
    
    def _should_initialize_database(self, db_manager: DatabaseManager) -> bool:
        """Check if database needs initialization."""
        try:
            stats = db_manager.get_database_stats()
            
            # If database is empty, initialize it
            if stats['total_tapes'] == 0 and stats['total_archives'] == 0:
                return True
            
            logger.info(f"Database already contains data: {stats['total_tapes']} tapes, {stats['total_archives']} archives")
            return False
            
        except Exception as e:
            logger.warning(f"Could not check database status: {e}")
            return True
    
    def _initialize_sample_data(self, db_manager: DatabaseManager):
        """Initialize database with sample/default data."""
        try:
            # Create a default "Unknown" tape for existing archives without tape info
            unknown_tape_id = db_manager.add_tape(
                "UNKNOWN_TAPE",
                "Unknown",
                "Default tape for archives without tape information"
            )
            
            logger.info(f"Created default tape record (ID: {unknown_tape_id})")
            
        except Exception as e:
            logger.warning(f"Failed to create sample data: {e}")
    
    def _setup_metadata(self, db_manager: DatabaseManager):
        """Set up database metadata and version information."""
        try:
            with sqlite3.connect(db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Create metadata table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS metadata (
                        key VARCHAR(50) PRIMARY KEY,
                        value TEXT,
                        updated_date DATETIME
                    )
                """)
                
                # Set schema version
                now = datetime.now()
                cursor.execute("""
                    INSERT OR REPLACE INTO metadata (key, value, updated_date)
                    VALUES (?, ?, ?)
                """, ('schema_version', str(self.CURRENT_SCHEMA_VERSION), now))
                
                # Set database creation date
                cursor.execute("""
                    INSERT OR IGNORE INTO metadata (key, value, updated_date)
                    VALUES (?, ?, ?)
                """, ('created_date', now.isoformat(), now))
                
                # Set application version
                cursor.execute("""
                    INSERT OR REPLACE INTO metadata (key, value, updated_date)
                    VALUES (?, ?, ?)
                """, ('app_version', '2.0.0', now))
                
                conn.commit()
                logger.info(f"Database metadata initialized (schema version: {self.CURRENT_SCHEMA_VERSION})")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to setup metadata: {e}")
            raise
    
    def migrate_schema(self, db_manager: DatabaseManager, from_version: int, to_version: int):
        """Migrate database schema between versions.
        
        Args:
            db_manager: Database manager instance
            from_version: Current schema version
            to_version: Target schema version
        """
        if from_version == to_version:
            logger.info("Database schema is up to date")
            return
        
        logger.info(f"Migrating database schema from version {from_version} to {to_version}")
        
        try:
            # Create backup before migration
            backup_path = db_manager.backup_database(
                str(db_manager.db_path.parent / f"pre_migration_v{from_version}_backup.db")
            )
            logger.info(f"Pre-migration backup created: {backup_path}")
            
            # Perform migration steps
            with sqlite3.connect(db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Migration logic would go here
                # For now, we only have version 1, so no migrations needed
                if from_version < 1 and to_version >= 1:
                    # Example migration: Add new column
                    # cursor.execute("ALTER TABLE tapes ADD COLUMN new_field TEXT")
                    pass
                
                # Update schema version
                cursor.execute("""
                    UPDATE metadata 
                    SET value = ?, updated_date = ?
                    WHERE key = 'schema_version'
                """, (str(to_version), datetime.now()))
                
                conn.commit()
            
            logger.info(f"Database migration completed successfully")
            
        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            raise
    
    def get_database_info(self, db_manager: DatabaseManager) -> dict:
        """Get database information and metadata.
        
        Returns:
            Dictionary with database information
        """
        try:
            info = {
                'db_path': str(db_manager.db_path),
                'db_size_bytes': db_manager.db_path.stat().st_size if db_manager.db_path.exists() else 0,
                'stats': db_manager.get_database_stats()
            }
            
            # Get metadata
            with sqlite3.connect(db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                try:
                    cursor.execute("SELECT * FROM metadata")
                    metadata = {row['key']: row['value'] for row in cursor.fetchall()}
                    info['metadata'] = metadata
                except sqlite3.OperationalError:
                    # Metadata table doesn't exist
                    info['metadata'] = {}
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {'error': str(e)}
    
    def check_database_integrity(self, db_manager: DatabaseManager) -> bool:
        """Check database integrity and consistency.
        
        Returns:
            True if database is healthy, False otherwise
        """
        try:
            logger.info("Checking database integrity...")
            
            with sqlite3.connect(db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # SQLite integrity check
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                
                if integrity_result != "ok":
                    logger.error(f"Database integrity check failed: {integrity_result}")
                    return False
                
                # Check foreign key constraints
                cursor.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()
                
                if fk_violations:
                    logger.error(f"Foreign key violations found: {fk_violations}")
                    return False
                
                # Check for orphaned records
                orphaned_issues = []
                
                # Check for archives without tapes
                cursor.execute("""
                    SELECT COUNT(*) FROM archives a
                    LEFT JOIN tapes t ON a.tape_id = t.tape_id
                    WHERE t.tape_id IS NULL
                """)
                orphaned_archives = cursor.fetchone()[0]
                if orphaned_archives > 0:
                    orphaned_issues.append(f"{orphaned_archives} archives without tape records")
                
                # Check for files without archives
                cursor.execute("""
                    SELECT COUNT(*) FROM files f
                    LEFT JOIN archives a ON f.archive_id = a.archive_id
                    WHERE a.archive_id IS NULL
                """)
                orphaned_files = cursor.fetchone()[0]
                if orphaned_files > 0:
                    orphaned_issues.append(f"{orphaned_files} files without archive records")
                
                if orphaned_issues:
                    logger.warning(f"Database consistency issues found: {', '.join(orphaned_issues)}")
                    return False
                
                logger.info("Database integrity check passed")
                return True
                
        except Exception as e:
            logger.error(f"Database integrity check failed: {e}")
            return False
    
    def repair_database(self, db_manager: DatabaseManager) -> bool:
        """Attempt to repair database issues.
        
        Returns:
            True if repair was successful, False otherwise
        """
        try:
            logger.info("Attempting to repair database...")
            
            # Create backup before repair
            backup_path = db_manager.backup_database(
                str(db_manager.db_path.parent / f"pre_repair_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            )
            logger.info(f"Pre-repair backup created: {backup_path}")
            
            with sqlite3.connect(db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Repair orphaned archives by assigning to unknown tape
                unknown_tape = db_manager.find_tape_by_label("UNKNOWN_TAPE")
                if unknown_tape:
                    unknown_tape_id = unknown_tape['tape_id']
                    
                    cursor.execute("""
                        UPDATE archives 
                        SET tape_id = ?
                        WHERE tape_id NOT IN (SELECT tape_id FROM tapes)
                    """, (unknown_tape_id,))
                    
                    repaired_archives = cursor.rowcount
                    if repaired_archives > 0:
                        logger.info(f"Repaired {repaired_archives} orphaned archives")
                
                # Remove orphaned files
                cursor.execute("""
                    DELETE FROM files 
                    WHERE archive_id NOT IN (SELECT archive_id FROM archives)
                """)
                
                removed_files = cursor.rowcount
                if removed_files > 0:
                    logger.info(f"Removed {removed_files} orphaned file records")
                
                # Vacuum database to reclaim space
                cursor.execute("VACUUM")
                
                conn.commit()
            
            # Verify repair was successful
            if self.check_database_integrity(db_manager):
                logger.info("Database repair completed successfully")
                return True
            else:
                logger.error("Database repair failed - integrity issues remain")
                return False
                
        except Exception as e:
            logger.error(f"Database repair failed: {e}")
            return False
    
    def optimize_database(self, db_manager: DatabaseManager):
        """Optimize database performance."""
        try:
            logger.info("Optimizing database...")
            
            with sqlite3.connect(db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Analyze tables for query optimization
                cursor.execute("ANALYZE")
                
                # Rebuild indexes
                cursor.execute("REINDEX")
                
                # Vacuum database
                cursor.execute("VACUUM")
                
                conn.commit()
            
            logger.info("Database optimization completed")
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            raise
    
    def cleanup_old_backups(self, max_backups: int = 10):
        """Clean up old database backups.
        
        Args:
            max_backups: Maximum number of backups to keep
        """
        try:
            db_manager = DatabaseManager(self.db_path) if self.db_path else DatabaseManager()
            backup_dir = db_manager.db_path.parent / "backups"
            
            if not backup_dir.exists():
                return
            
            # Get all backup files
            backup_files = list(backup_dir.glob("*.db"))
            
            if len(backup_files) <= max_backups:
                return
            
            # Sort by modification time (oldest first)
            backup_files.sort(key=lambda f: f.stat().st_mtime)
            
            # Remove oldest backups
            files_to_remove = backup_files[:-max_backups]
            
            for backup_file in files_to_remove:
                backup_file.unlink()
                logger.info(f"Removed old backup: {backup_file.name}")
            
            logger.info(f"Cleaned up {len(files_to_remove)} old backup files")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")


def main():
    """Main function for testing database initialization."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        initializer = DatabaseInitializer()
        db_manager = initializer.setup_database()
        
        # Display database info
        info = initializer.get_database_info(db_manager)
        print("Database Information:")
        for key, value in info.items():
            if key == 'stats':
                print(f"  {key}:")
                for stat_key, stat_value in value.items():
                    print(f"    {stat_key}: {stat_value}")
            else:
                print(f"  {key}: {value}")
        
        # Check integrity
        if initializer.check_database_integrity(db_manager):
            print("\n✅ Database integrity check passed")
        else:
            print("\n❌ Database integrity check failed")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")


if __name__ == "__main__":
    main()

