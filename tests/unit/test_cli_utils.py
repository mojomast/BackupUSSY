import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.unit


class TestConfigManager:
    """Test CLI configuration manager."""
    
    def test_config_manager_import(self):
        """Test that ConfigManager can be imported."""
        try:
            from src.cli_utils.config import ConfigManager
            assert ConfigManager is not None
        except ImportError as e:
            pytest.fail(f"Failed to import ConfigManager: {e}")
    
    def test_config_manager_initialization(self):
        """Test ConfigManager initialization."""
        try:
            from src.cli_utils.config import ConfigManager
            
            # Test with no config file
            config = ConfigManager(None)
            assert config is not None
            
            # Test with custom config file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
                f.write('[tape]\ndefault_device = /dev/st0\n')
                config_file = f.name
            
            try:
                config = ConfigManager(config_file)
                assert config is not None
            finally:
                os.unlink(config_file)
                
        except Exception as e:
            pytest.fail(f"ConfigManager initialization test failed: {e}")
    
    def test_config_manager_methods(self):
        """Test ConfigManager has required methods."""
        try:
            from src.cli_utils.config import ConfigManager
            
            config = ConfigManager(None)
            
            # Check that required methods exist
            assert hasattr(config, 'get_default_device')
            assert hasattr(config, 'get_database_path')
            assert hasattr(config, 'get_log_level')
            
        except Exception as e:
            pytest.fail(f"ConfigManager methods test failed: {e}")


class TestProgressManager:
    """Test CLI progress manager."""
    
    def test_progress_manager_import(self):
        """Test that ProgressManager can be imported."""
        try:
            from src.cli_utils.progress import ProgressManager
            assert ProgressManager is not None
        except ImportError as e:
            pytest.fail(f"Failed to import ProgressManager: {e}")
    
    def test_progress_manager_initialization(self):
        """Test ProgressManager initialization."""
        try:
            from src.cli_utils.progress import ProgressManager
            
            # Test with different options
            progress = ProgressManager(quiet=False, no_color=False)
            assert progress is not None
            
            progress_quiet = ProgressManager(quiet=True, no_color=True)
            assert progress_quiet is not None
            
        except Exception as e:
            pytest.fail(f"ProgressManager initialization test failed: {e}")
    
    def test_progress_manager_methods(self):
        """Test ProgressManager has required methods."""
        try:
            from src.cli_utils.progress import ProgressManager
            
            progress = ProgressManager(quiet=False, no_color=False)
            
            # Check that required methods exist
            assert hasattr(progress, 'show_progress')
            assert hasattr(progress, 'print_success')
            assert hasattr(progress, 'print_error')
            assert hasattr(progress, 'print_warning')
            assert hasattr(progress, 'print_info')
            
        except Exception as e:
            pytest.fail(f"ProgressManager methods test failed: {e}")
    
    @patch('builtins.print')
    def test_progress_manager_output(self, mock_print):
        """Test ProgressManager output methods."""
        try:
            from src.cli_utils.progress import ProgressManager
            
            progress = ProgressManager(quiet=False, no_color=False)
            
            # Test output methods don't crash
            progress.print_success("Test success")
            progress.print_error("Test error")
            progress.print_warning("Test warning")
            progress.print_info("Test info")
            
            # Verify print was called
            assert mock_print.called
            
        except Exception as e:
            pytest.fail(f"ProgressManager output test failed: {e}")
    
    @patch('builtins.print')
    def test_progress_manager_quiet_mode(self, mock_print):
        """Test ProgressManager quiet mode."""
        try:
            from src.cli_utils.progress import ProgressManager
            
            progress = ProgressManager(quiet=True, no_color=True)
            
            # Test that info messages are suppressed in quiet mode
            progress.print_info("This should be suppressed")
            
            # Errors should still be shown
            progress.print_error("This should be shown")
            
        except Exception as e:
            pytest.fail(f"ProgressManager quiet mode test failed: {e}")


class TestLoggingSetup:
    """Test CLI logging setup."""
    
    def test_logging_setup_import(self):
        """Test that logging setup can be imported."""
        try:
            from src.cli_utils.logging import setup_cli_logging
            assert setup_cli_logging is not None
        except ImportError as e:
            pytest.fail(f"Failed to import setup_cli_logging: {e}")
    
    def test_logging_setup_function(self):
        """Test logging setup function."""
        try:
            from src.cli_utils.logging import setup_cli_logging
            
            # Create mock args
            args = MagicMock()
            args.verbose = 0
            args.quiet = False
            args.log_file = None
            
            # Should not crash
            logger = setup_cli_logging(args)
            assert logger is not None
            
        except Exception as e:
            pytest.fail(f"Logging setup test failed: {e}")
    
    def test_logging_setup_with_file(self):
        """Test logging setup with log file."""
        try:
            from src.cli_utils.logging import setup_cli_logging
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
                log_file = f.name
            
            args = MagicMock()
            args.verbose = 1
            args.quiet = False
            args.log_file = log_file
            
            try:
                logger = setup_cli_logging(args)
                assert logger is not None
            finally:
                if os.path.exists(log_file):
                    os.unlink(log_file)
                    
        except Exception as e:
            pytest.fail(f"Logging setup with file test failed: {e}")
    
    def test_logging_setup_verbose_levels(self):
        """Test logging setup with different verbose levels."""
        try:
            from src.cli_utils.logging import setup_cli_logging
            
            # Test different verbosity levels
            for verbose_level in [0, 1, 2, 3]:
                args = MagicMock()
                args.verbose = verbose_level
                args.quiet = False
                args.log_file = None
                
                logger = setup_cli_logging(args)
                assert logger is not None
                
        except Exception as e:
            pytest.fail(f"Logging verbose levels test failed: {e}")


class TestBaseCommand:
    """Test base command class."""
    
    def test_base_command_import(self):
        """Test that BaseCommand can be imported."""
        try:
            from src.cli_commands.base import BaseCommand
            assert BaseCommand is not None
        except ImportError as e:
            pytest.fail(f"Failed to import BaseCommand: {e}")
    
    def test_base_command_initialization(self):
        """Test BaseCommand initialization."""
        try:
            from src.cli_commands.base import BaseCommand
            
            managers = {
                'dep_manager': MagicMock(),
                'logger': MagicMock()
            }
            
            base_cmd = BaseCommand(managers)
            assert base_cmd is not None
            assert hasattr(base_cmd, 'managers')
            
        except Exception as e:
            pytest.fail(f"BaseCommand initialization test failed: {e}")
    
    def test_base_command_methods(self):
        """Test BaseCommand has required methods."""
        try:
            from src.cli_commands.base import BaseCommand
            
            managers = {'logger': MagicMock()}
            base_cmd = BaseCommand(managers)
            
            # Check that required methods exist
            assert hasattr(base_cmd, 'print_success')
            assert hasattr(base_cmd, 'print_error')
            assert hasattr(base_cmd, 'print_warning')
            assert hasattr(base_cmd, 'print_info')
            assert hasattr(base_cmd, 'print_header')
            assert hasattr(base_cmd, 'execute')
            
        except Exception as e:
            pytest.fail(f"BaseCommand methods test failed: {e}")
    
    def test_base_command_execute_abstract(self):
        """Test BaseCommand execute method is abstract."""
        try:
            from src.cli_commands.base import BaseCommand
            
            managers = {'logger': MagicMock()}
            base_cmd = BaseCommand(managers)
            
            # Should raise NotImplementedError
            with pytest.raises(NotImplementedError):
                base_cmd.execute(None)
                
        except Exception as e:
            pytest.fail(f"BaseCommand abstract method test failed: {e}")


class TestCLIExceptions:
    """Test CLI exceptions."""
    
    def test_exceptions_import(self):
        """Test that exceptions can be imported."""
        try:
            from src.exceptions import BackupussyError
            assert BackupussyError is not None
        except ImportError as e:
            pytest.fail(f"Failed to import exceptions: {e}")
    
    def test_backupussy_error(self):
        """Test BackupussyError exception."""
        try:
            from src.exceptions import BackupussyError
            
            # Test exception creation
            error = BackupussyError("Test error")
            assert str(error) == "Test error"
            
            # Test raising exception
            with pytest.raises(BackupussyError):
                raise BackupussyError("Test error")
                
        except Exception as e:
            pytest.fail(f"BackupussyError test failed: {e}")

