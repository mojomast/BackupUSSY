#!/usr/bin/env python3
"""
Recovery Test Suite - Comprehensive testing for Phase 2 features.
Phase 2.6.1 - Recovery and database testing for LTO Tape Archive Tool.
"""

import os
import tempfile
import shutil
import logging
import unittest
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

from main import DependencyManager
from database_manager import DatabaseManager
from recovery_manager import RecoveryManager
from search_interface import SearchInterface
from tape_browser import TapeBrowser
from tape_library import TapeLibrary
from archive_manager import ArchiveManager
from advanced_search import AdvancedSearchManager

logger = logging.getLogger(__name__)

class RecoveryTestSuite(unittest.TestCase):
    """Comprehensive test suite for Phase 2 recovery and database features."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.test_dir = Path(tempfile.mkdtemp(prefix="lto_test_"))
        cls.db_path = cls.test_dir / "test_tape_index.db"
        cls.sample_files_dir = cls.test_dir / "sample_files"
        
        # Create sample files for testing
        cls._create_sample_files()
        
        # Initialize components
        cls.dep_manager = DependencyManager()
        cls.db_manager = DatabaseManager(str(cls.db_path))
        cls.recovery_manager = RecoveryManager(cls.dep_manager, cls.db_manager)
        cls.search_interface = SearchInterface(cls.db_manager, cls.recovery_manager)
        cls.tape_library = TapeLibrary(cls.db_manager)
        
        logger.info(f"Test environment set up at: {cls.test_dir}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)
        logger.info("Test environment cleaned up")
    
    @classmethod
    def _create_sample_files(cls):
        """Create sample files for testing."""
        cls.sample_files_dir.mkdir(parents=True, exist_ok=True)
        
        # Create various file types
        sample_files = {
            'document.txt': 'This is a sample text document for testing.',
            'image.jpg': b'\xFF\xD8\xFF\xE0\x00\x10JFIF' + b'\x00' * 100,  # Mock JPEG
            'data.csv': 'name,value\ntest1,100\ntest2,200\n',
            'script.py': 'print("Hello, World!")\n',
            'config.json': '{"setting": "value", "number": 42}'
        }
        
        for filename, content in sample_files.items():
            file_path = cls.sample_files_dir / filename
            if isinstance(content, str):
                file_path.write_text(content)
            else:
                file_path.write_bytes(content)
        
        # Create subdirectory with files
        subdir = cls.sample_files_dir / "subdir"
        subdir.mkdir(exist_ok=True)
        (subdir / "nested_file.txt").write_text("This is a nested file.")
        
        logger.info(f"Created {len(sample_files) + 1} sample files")
    
    def test_database_initialization(self):
        """Test database creation and table structure."""
        # Database should be created during setup
        self.assertTrue(self.db_path.exists())
        
        # Check table structure
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if all required tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['tapes', 'archives', 'files']
            for table in required_tables:
                self.assertIn(table, tables, f"Required table '{table}' not found")
        
        logger.info("✅ Database initialization test passed")
    
    def test_tape_operations(self):
        """Test basic tape database operations."""
        # Add a test tape
        tape_id = self.db_manager.add_tape(
            tape_label="TEST_TAPE_001",
            device="\\\\.\\Tape0",
            notes="Test tape for unit testing"
        )
        
        self.assertIsInstance(tape_id, int)
        self.assertGreater(tape_id, 0)
        
        # Retrieve the tape
        tape = self.db_manager.find_tape_by_label("TEST_TAPE_001")
        self.assertIsNotNone(tape)
        self.assertEqual(tape['tape_label'], "TEST_TAPE_001")
        self.assertEqual(tape['tape_device'], "\\\\.\\Tape0")
        
        # Update tape status
        self.db_manager.update_tape_status(tape_id, "full", "Tape is now full")
        
        # Verify update
        updated_tape = self.db_manager.find_tape_by_label("TEST_TAPE_001")
        self.assertEqual(updated_tape['tape_status'], "full")
        
        logger.info("✅ Tape operations test passed")
    
    def test_archive_operations(self):
        """Test archive database operations."""
        # Create a test tape first
        tape_id = self.db_manager.add_tape("TEST_TAPE_002", "\\\\.\\Tape1")
        
        # Add an archive
        archive_id = self.db_manager.add_archive(
            tape_id=tape_id,
            archive_name="test_archive.tar",
            source_folder=str(self.sample_files_dir),
            archive_size_bytes=1024000,
            file_count=5,
            checksum="abc123def456",
            compression_used=False
        )
        
        self.assertIsInstance(archive_id, int)
        self.assertGreater(archive_id, 0)
        
        # Add files to the archive
        test_files = [
            {
                'file_path': 'document.txt',
                'file_size_bytes': 1024,
                'file_modified': '2024-01-01 12:00:00',
                'file_type': '.txt',
                'file_checksum': 'file_abc123'
            },
            {
                'file_path': 'image.jpg',
                'file_size_bytes': 2048,
                'file_modified': '2024-01-02 12:00:00',
                'file_type': '.jpg',
                'file_checksum': 'file_def456'
            }
        ]
        
        self.db_manager.add_files(archive_id, test_files)
        
        # Verify archive details
        archive_details = self.db_manager.get_archive_details(archive_id)
        self.assertEqual(archive_details['archive_info']['archive_name'], "test_archive.tar")
        self.assertEqual(len(archive_details['files']), 2)
        
        logger.info("✅ Archive operations test passed")
    
    def test_search_functionality(self):
        """Test search interface functionality."""
        # Set up test data (use existing data from previous tests)
        
        # Test basic file search
        results = self.db_manager.search_files("document")
        self.assertGreater(len(results), 0)
        
        # Test search with file type filter
        results = self.db_manager.search_files("image", file_type=".jpg")
        
        # Test search interface methods
        search_results = self.search_interface.search_files("document", {})
        self.assertIsInstance(search_results, list)
        
        # Test advanced search patterns
        if hasattr(self.search_interface, 'search_with_regex'):
            regex_results = self.search_interface.search_with_regex(r".*\.txt$")
            self.assertIsInstance(regex_results, list)
        
        logger.info("✅ Search functionality test passed")
    
    def test_tape_library_features(self):
        """Test tape library management features."""
        # Test duplicate detection
        duplicates = self.tape_library.detect_duplicate_archives()
        self.assertIsInstance(duplicates, list)
        
        # Test tape optimization
        optimization = self.tape_library.optimize_tape_usage()
        self.assertIsInstance(optimization, dict)
        self.assertIn('underutilized_tapes', optimization)
        self.assertIn('consolidation_suggestions', optimization)
        
        # Test tape reports
        reports = self.tape_library.generate_tape_reports()
        self.assertIsInstance(reports, dict)
        self.assertIn('summary', reports)
        
        # Test maintenance tasks
        maintenance = self.tape_library.schedule_maintenance_tasks()
        self.assertIsInstance(maintenance, dict)
        self.assertIn('immediate', maintenance)
        self.assertIn('weekly', maintenance)
        
        logger.info("✅ Tape library features test passed")
    
    @patch('subprocess.run')
    def test_recovery_operations(self, mock_subprocess):
        """Test recovery manager operations."""
        # Mock successful tape operations
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "file1.txt\nfile2.txt\n"
        mock_subprocess.return_value.stderr = ""
        
        # Test tape integrity check
        integrity_result = self.recovery_manager.verify_tape_integrity("\\\\.\\Tape0")
        self.assertIsInstance(integrity_result, dict)
        self.assertIn('device', integrity_result)
        self.assertIn('readable', integrity_result)
        
        # Test damage detection
        damage_report = self.recovery_manager.detect_tape_damage("\\\\.\\Tape0")
        self.assertIsInstance(damage_report, dict)
        self.assertIn('is_damaged', damage_report)
        self.assertIn('recommendations', damage_report)
        
        # Test readability test
        readability = self.recovery_manager.test_tape_readability("\\\\.\\Tape0")
        self.assertIsInstance(readability, dict)
        self.assertIn('readable', readability)
        
        logger.info("✅ Recovery operations test passed")
    
    def test_database_export_import(self):
        """Test database export and import functionality."""
        export_path = self.test_dir / "test_export.json"
        
        # Test JSON export
        success = self.db_manager.export_inventory_json(str(export_path))
        self.assertTrue(success)
        self.assertTrue(export_path.exists())
        
        # Test CSV export
        csv_export_path = self.test_dir / "test_export.csv"
        success = self.db_manager.export_inventory_csv(str(csv_export_path))
        self.assertTrue(success)
        
        # Create a new database for import testing
        import_db_path = self.test_dir / "import_test.db"
        import_db = DatabaseManager(str(import_db_path))
        
        # Test JSON import
        if export_path.exists():
            records_imported = import_db.import_inventory_json(str(export_path))
            self.assertGreaterEqual(records_imported, 0)
        
        logger.info("✅ Database export/import test passed")
    
    def test_database_statistics(self):
        """Test database statistics and reporting."""
        stats = self.db_manager.get_database_stats()
        self.assertIsInstance(stats, dict)
        
        required_stats = [
            'total_tapes', 'total_archives', 'total_files', 
            'total_data_bytes', 'active_tapes'
        ]
        
        for stat in required_stats:
            self.assertIn(stat, stats)
            self.assertIsInstance(stats[stat], int)
        
        # Test library statistics
        lib_stats = self.db_manager.get_library_statistics()
        self.assertIsInstance(lib_stats, dict)
        
        logger.info("✅ Database statistics test passed")
    
    def test_error_handling(self):
        """Test error handling and edge cases."""
        # Test with non-existent tape
        tape = self.db_manager.find_tape_by_label("NON_EXISTENT_TAPE")
        self.assertIsNone(tape)
        
        # Test with invalid archive ID
        archive_details = self.db_manager.get_archive_details(99999)
        # Should not raise exception, might return None or empty result
        
        # Test recovery manager with invalid device
        with patch('builtins.open', side_effect=OSError("Device not found")):
            accessible = self.recovery_manager._test_tape_access("\\invalid\\device")
            self.assertFalse(accessible)
        
        logger.info("✅ Error handling test passed")
    
    def test_integration_workflow(self):
        """Test complete integration workflow."""
        # This is a comprehensive end-to-end test
        
        # 1. Create tape and archive (already done in previous tests)
        tape_id = self.db_manager.add_tape("INTEGRATION_TAPE", "\\\\.\\Tape2")
        
        # 2. Add archive with files
        archive_id = self.db_manager.add_archive(
            tape_id=tape_id,
            archive_name="integration_test.tar",
            source_folder=str(self.sample_files_dir),
            archive_size_bytes=2048000,
            file_count=6,
            checksum="integration_checksum",
            compression_used=True
        )
        
        # 3. Add file records
        sample_files = [
            {
                'file_path': 'integration_file.txt',
                'file_size_bytes': 512,
                'file_modified': '2024-06-09 12:00:00',
                'file_type': '.txt',
                'file_checksum': 'integration_file_hash'
            }
        ]
        self.db_manager.add_files(archive_id, sample_files)
        
        # 4. Search for the file
        search_results = self.db_manager.search_files("integration_file")
        self.assertGreater(len(search_results), 0)
        
        # 5. Get tape contents
        contents = self.db_manager.get_tape_contents(tape_id)
        self.assertIn('archives', contents)
        self.assertGreater(len(contents['archives']), 0)
        
        # 6. Test library optimization
        optimization = self.tape_library.optimize_tape_usage()
        self.assertIsInstance(optimization, dict)
        
        logger.info("✅ Integration workflow test passed")
    
    def test_performance_benchmarks(self):
        """Test performance with larger datasets."""
        import time
        
        # Create a tape with many files for performance testing
        tape_id = self.db_manager.add_tape("PERF_TAPE", "\\\\.\\Tape3")
        archive_id = self.db_manager.add_archive(
            tape_id=tape_id,
            archive_name="performance_test.tar",
            source_folder="/test/large_folder",
            archive_size_bytes=10000000,
            file_count=1000,
            checksum="perf_checksum"
        )
        
        # Create 1000 file records
        large_file_list = []
        for i in range(1000):
            large_file_list.append({
                'file_path': f'file_{i:04d}.txt',
                'file_size_bytes': 1024 * (i + 1),
                'file_modified': '2024-01-01 12:00:00',
                'file_type': '.txt',
                'file_checksum': f'hash_{i:04d}'
            })
        
        # Time the bulk insert
        start_time = time.time()
        self.db_manager.add_files(archive_id, large_file_list)
        insert_time = time.time() - start_time
        
        # Time a search operation
        start_time = time.time()
        search_results = self.db_manager.search_files("file_0500")
        search_time = time.time() - start_time
        
        # Performance assertions (adjust thresholds as needed)
        self.assertLess(insert_time, 5.0, "Bulk insert took too long")
        self.assertLess(search_time, 1.0, "Search took too long")
        self.assertGreater(len(search_results), 0, "Search should find the file")
        
        logger.info(f"✅ Performance test passed (insert: {insert_time:.2f}s, search: {search_time:.2f}s)")

class QuickValidationSuite(unittest.TestCase):
    """Quick validation tests for development workflow."""
    
    def setUp(self):
        """Set up for quick tests."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="lto_quick_"))
        self.db_path = self.test_dir / "quick_test.db"
        self.db_manager = DatabaseManager(str(self.db_path))
    
    def tearDown(self):
        """Clean up quick tests."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_database_creation(self):
        """Quick test for database creation."""
        self.assertTrue(self.db_path.exists())
        
        # Test basic operations
        tape_id = self.db_manager.add_tape("QUICK_TEST", "\\\\.\\Tape0")
        self.assertIsInstance(tape_id, int)
        
    def test_component_imports(self):
        """Test that all components can be imported."""
        try:
            from database_manager import DatabaseManager
            from recovery_manager import RecoveryManager
            from search_interface import SearchInterface
            from tape_browser import TapeBrowser
            from tape_library import TapeLibrary
            from advanced_search import AdvancedSearchManager
        except ImportError as e:
            self.fail(f"Component import failed: {e}")
    
    def test_basic_functionality(self):
        """Test basic functionality is working."""
        # Test database operations
        tape_id = self.db_manager.add_tape("BASIC_TEST", "\\\\.\\Tape0")
        archive_id = self.db_manager.add_archive(
            tape_id, "test.tar", "/test", 1024, 1, "hash"
        )
        
        files = [{'file_path': 'test.txt', 'file_size_bytes': 100, 
                 'file_modified': '2024-01-01', 'file_type': '.txt'}]
        self.db_manager.add_files(archive_id, files)
        
        # Test search
        results = self.db_manager.search_files("test")
        self.assertGreater(len(results), 0)
        
        logger.info("✅ Basic functionality test passed")

def run_full_test_suite():
    """Run the complete test suite."""
    print("🧪 Starting LTO Tape Archive Tool - Phase 2 Test Suite")
    print("=" * 60)
    
    # Configure logging for tests
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test methods from RecoveryTestSuite
    test_loader = unittest.TestLoader()
    test_suite.addTests(test_loader.loadTestsFromTestCase(RecoveryTestSuite))
    test_suite.addTests(test_loader.loadTestsFromTestCase(QuickValidationSuite))
    
    # Run tests
    runner = unittest.TextTestRunner(
        verbosity=2,
        buffer=True,
        descriptions=True
    )
    
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"🎯 TEST SUMMARY:")
    print(f"   Tests Run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED! Phase 2 features are working correctly.")
        return True
    else:
        print("\n❌ SOME TESTS FAILED. Please review the output above.")
        return False

def run_quick_validation():
    """Run quick validation tests for development."""
    print("⚡ Quick Validation Suite")
    print("-" * 30)
    
    test_suite = unittest.TestSuite()
    test_loader = unittest.TestLoader()
    test_suite.addTests(test_loader.loadTestsFromTestCase(QuickValidationSuite))
    
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        success = run_quick_validation()
    else:
        success = run_full_test_suite()
    
    sys.exit(0 if success else 1)

