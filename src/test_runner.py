#!/usr/bin/env python3
"""
Test Runner - Basic functionality testing for the LTO Archive Tool.
"""

import os
import sys
import tempfile
import shutil
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from main import DependencyManager
from archive_manager import ArchiveManager, ArchiveMode
from tape_manager import TapeManager
from logger_manager import LoggerManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestRunner:
    """Basic functionality tests for the archive tool."""
    
    def __init__(self):
        self.test_dir = None
        self.dep_manager = None
        self.archive_manager = None
        self.tape_manager = None
        self.logger_manager = None
        
        self.results = {
            'dependencies': False,
            'folder_validation': False,
            'archive_creation': False,
            'tape_detection': False,
            'logging': False
        }
    
    def setup_test_environment(self):
        """Create temporary test folder with sample files."""
        self.test_dir = tempfile.mkdtemp(prefix="lto_test_")
        
        # Create some test files
        test_files = [
            "test_document.txt",
            "subfolder/nested_file.txt",
            "binary_file.dat"
        ]
        
        for file_path in test_files:
            full_path = Path(self.test_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if file_path.endswith('.txt'):
                content = f"This is a test file: {file_path}\n" * 100
            else:
                content = b"\x00\x01\x02\x03" * 1000
            
            if isinstance(content, str):
                full_path.write_text(content, encoding='utf-8')
            else:
                full_path.write_bytes(content)
        
        logger.info(f"Created test directory: {self.test_dir}")
        return self.test_dir
    
    def test_dependencies(self):
        """Test dependency detection."""
        logger.info("Testing dependency detection...")
        
        try:
            self.dep_manager = DependencyManager()
            dependencies_ok = self.dep_manager.detect_dependencies()
            
            if dependencies_ok:
                logger.info("✓ Dependencies detected successfully")
                dep_info = self.dep_manager.get_dependency_info()
                for name, path in dep_info.items():
                    logger.info(f"  {name}: {path or 'Not found'}")
                self.results['dependencies'] = True
            else:
                logger.error("✗ Dependencies missing")
                
        except Exception as e:
            logger.error(f"✗ Dependency test failed: {e}")
        
        return self.results['dependencies']
    
    def test_folder_validation(self):
        """Test folder validation functionality."""
        logger.info("Testing folder validation...")
        
        if not self.dep_manager:
            logger.error("Dependencies not initialized")
            return False
        
        try:
            self.archive_manager = ArchiveManager(self.dep_manager)
            
            # Test valid folder
            valid, message = self.archive_manager.validate_source_folder(self.test_dir)
            if valid:
                logger.info("✓ Valid folder validation passed")
            else:
                logger.error(f"✗ Valid folder validation failed: {message}")
                return False
            
            # Test invalid folder
            invalid_path = "/nonexistent/path"
            valid, message = self.archive_manager.validate_source_folder(invalid_path)
            if not valid:
                logger.info("✓ Invalid folder validation passed")
            else:
                logger.error("✗ Invalid folder validation should have failed")
                return False
            
            # Test size estimation
            size, count = self.archive_manager.estimate_archive_size(self.test_dir)
            logger.info(f"  Estimated size: {size} bytes, {count} files")
            
            if size > 0 and count > 0:
                logger.info("✓ Size estimation working")
                self.results['folder_validation'] = True
            else:
                logger.error("✗ Size estimation failed")
                
        except Exception as e:
            logger.error(f"✗ Folder validation test failed: {e}")
        
        return self.results['folder_validation']
    
    def test_archive_creation(self):
        """Test archive creation (without writing to tape)."""
        logger.info("Testing archive creation...")
        
        if not self.archive_manager:
            logger.error("Archive manager not initialized")
            return False
        
        try:
            # Test cached archive creation
            output_dir = tempfile.mkdtemp(prefix="lto_archive_test_")
            
            def progress_callback(message):
                logger.info(f"  Progress: {message}")
            
            archive_path, checksum = self.archive_manager.create_cached_archive(
                self.test_dir,
                output_dir=output_dir,
                compression=False,
                progress_callback=progress_callback
            )
            
            if os.path.exists(archive_path) and checksum:
                logger.info(f"✓ Archive created: {archive_path}")
                logger.info(f"  Checksum: {checksum[:16]}...")
                
                # Verify archive info
                archive_info = self.archive_manager.get_archive_info()
                if archive_info:
                    logger.info(f"  Archive size: {archive_info['size']} bytes")
                    self.results['archive_creation'] = True
                else:
                    logger.error("✗ Archive info retrieval failed")
            else:
                logger.error("✗ Archive creation failed")
            
            # Cleanup
            if os.path.exists(archive_path):
                os.remove(archive_path)
            shutil.rmtree(output_dir)
            
        except Exception as e:
            logger.error(f"✗ Archive creation test failed: {e}")
        
        return self.results['archive_creation']
    
    def test_tape_detection(self):
        """Test tape device detection."""
        logger.info("Testing tape device detection...")
        
        try:
            self.tape_manager = TapeManager(self.dep_manager)
            
            # Detect devices
            devices = self.tape_manager.detect_tape_devices()
            logger.info(f"  Found {len(devices)} tape devices: {devices}")
            
            # Test status check (will likely fail without actual tape)
            status = self.tape_manager.get_tape_status()
            logger.info(f"  Tape status: {status['status']} - {status['details'][:50]}...")
            
            # If we get this far without exceptions, consider it a pass
            logger.info("✓ Tape detection working (no actual tape required for test)")
            self.results['tape_detection'] = True
            
        except Exception as e:
            logger.error(f"✗ Tape detection test failed: {e}")
        
        return self.results['tape_detection']
    
    def test_logging(self):
        """Test logging functionality."""
        logger.info("Testing logging functionality...")
        
        try:
            self.logger_manager = LoggerManager()
            
            # Start a test job log
            job_logger = self.logger_manager.start_job_log(self.test_dir, "test_job")
            
            # Log some test data
            self.logger_manager.log_job_details(job_logger,
                folder=self.test_dir,
                mode="test",
                compression=False
            )
            
            self.logger_manager.log_progress(job_logger, "Testing in progress")
            
            # Finish the job log
            self.logger_manager.finish_job_log(job_logger, "SUCCESS",
                archive_name="test_job",
                folder_path=self.test_dir,
                tape_device="test_device",
                mode="test",
                compression=False,
                copies=1,
                file_count=3,
                total_size_bytes=10000,
                duration_seconds=5
            )
            
            # Test statistics
            stats = self.logger_manager.get_job_statistics()
            logger.info(f"  Job statistics: {stats}")
            
            # Test recent jobs
            recent = self.logger_manager.get_recent_jobs(5)
            logger.info(f"  Recent jobs: {len(recent)} entries")
            
            logger.info("✓ Logging functionality working")
            self.results['logging'] = True
            
        except Exception as e:
            logger.error(f"✗ Logging test failed: {e}")
        
        return self.results['logging']
    
    def cleanup(self):
        """Clean up test environment."""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            logger.info(f"Cleaned up test directory: {self.test_dir}")
        
        if self.archive_manager:
            self.archive_manager.cleanup()
    
    def run_all_tests(self):
        """Run all functionality tests."""
        logger.info("Starting LTO Archive Tool functionality tests...")
        
        try:
            # Setup
            self.setup_test_environment()
            
            # Run tests
            self.test_dependencies()
            self.test_folder_validation()
            self.test_archive_creation()
            self.test_tape_detection()
            self.test_logging()
            
            # Summary
            logger.info("\n=== Test Results ===")
            passed = 0
            total = len(self.results)
            
            for test_name, result in self.results.items():
                status = "PASS" if result else "FAIL"
                logger.info(f"{test_name}: {status}")
                if result:
                    passed += 1
            
            logger.info(f"\nOverall: {passed}/{total} tests passed")
            
            if passed == total:
                logger.info("🎉 All core functionality tests PASSED!")
                logger.info("The tool is ready for basic operation.")
                return True
            else:
                logger.warning("⚠️ Some tests failed. Review errors above.")
                return False
                
        except Exception as e:
            logger.error(f"Test runner failed: {e}")
            return False
        
        finally:
            self.cleanup()


def main():
    """Main test entry point."""
    runner = TestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n✅ All tests passed! The LTO Archive Tool is ready to use.")
        print("\nTo start the GUI application, run:")
        print("  python src/gui.py")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == '__main__':
    main()

