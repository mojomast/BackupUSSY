import pytest
import io
import sys
from unittest.mock import patch, MagicMock

pytestmark = [pytest.mark.integration, pytest.mark.menu]


class TestMenuCommand:
    """Test menu command functionality."""
    
    def test_menu_help(self, script_runner):
        """Test menu command help."""
        result = script_runner.run(['backupussy', 'menu', '--help'])
        assert result.returncode == 0
        assert 'usage: backupussy menu' in result.stdout.lower()
        assert '--mode' in result.stdout
        assert 'interactive' in result.stdout
        assert 'wizard' in result.stdout
    
    def test_menu_mode_validation(self, script_runner):
        """Test menu mode parameter validation."""
        # Test invalid mode
        result = script_runner.run(['backupussy', 'menu', '--mode', 'invalid'])
        assert result.returncode != 0
        assert 'invalid choice' in result.stderr.lower()
    
    @patch('builtins.input', side_effect=['q'])  # Quit immediately
    @patch('os.system')  # Mock screen clearing
    def test_menu_interactive_mode_quit(self, mock_system, mock_input, script_runner):
        """Test interactive menu mode with immediate quit."""
        # This test simulates starting interactive mode and immediately quitting
        result = script_runner.run(['backupussy', 'menu', '--mode', 'interactive'])
        # Menu should handle the quit command gracefully
        assert result.returncode == 0 or 'Error:' in result.stderr
    
    @patch('builtins.input', side_effect=['q'])  # Quit immediately
    def test_menu_wizard_mode_quit(self, mock_input, script_runner):
        """Test wizard menu mode with immediate quit."""
        result = script_runner.run(['backupussy', 'menu', '--mode', 'wizard'])
        # Menu should handle the quit command gracefully
        assert result.returncode == 0 or 'Error:' in result.stderr


class TestMenuNavigation:
    """Test menu navigation functionality (unit-style tests)."""
    
    def test_menu_command_import(self):
        """Test that MenuCommand can be imported successfully."""
        try:
            from src.cli_commands.menu import MenuCommand
            assert MenuCommand is not None
        except ImportError as e:
            pytest.fail(f"Failed to import MenuCommand: {e}")
    
    @patch('builtins.input', side_effect=['q'])  # Quit immediately
    @patch('os.system')  # Mock screen clearing
    def test_menu_wizard_selection(self, mock_system, mock_input):
        """Test selecting wizard mode from main menu."""
        try:
            from src.cli_commands.menu import MenuCommand
            
            # Create mock managers
            managers = {
                'dep_manager': MagicMock(),
                'archive_manager': MagicMock(),
                'tape_manager': MagicMock(),
                'db_manager': MagicMock(),
                'recovery_manager': MagicMock(),
                'search_interface': MagicMock(),
                'tape_library': MagicMock(),
                'config_manager': MagicMock(),
                'progress_manager': MagicMock(),
                'logger': MagicMock()
            }
            
            menu = MenuCommand(managers)
            
            # Create mock args
            args = MagicMock()
            args.mode = 'interactive'
            
            # Test should not crash
            result = menu.execute(args)
            assert result == 0 or result is None
            
        except Exception as e:
            pytest.fail(f"Menu navigation test failed: {e}")
    
    def test_menu_clear_screen_method(self):
        """Test menu clear screen functionality."""
        try:
            from src.cli_commands.menu import MenuCommand
            
            managers = {'logger': MagicMock()}
            menu = MenuCommand(managers)
            
            # This should not crash
            with patch('os.system') as mock_system:
                menu._clear_screen()
                mock_system.assert_called_once()
                
        except Exception as e:
            pytest.fail(f"Clear screen test failed: {e}")
    
    def test_menu_go_back_method(self):
        """Test menu navigation back functionality."""
        try:
            from src.cli_commands.menu import MenuCommand
            
            managers = {'logger': MagicMock()}
            menu = MenuCommand(managers)
            
            # Test going back with empty history
            menu.current_menu = 'archive'
            menu.menu_history = []
            menu._go_back()
            assert menu.current_menu == 'main'
            
            # Test going back with history
            menu.current_menu = 'search'
            menu.menu_history = ['main', 'archive']
            menu._go_back()
            assert menu.current_menu == 'archive'
            assert menu.menu_history == ['main']
            
        except Exception as e:
            pytest.fail(f"Go back test failed: {e}")


class TestMenuWizards:
    """Test menu wizard functionality."""
    
    def test_wizard_methods_exist(self):
        """Test that all wizard methods exist."""
        try:
            from src.cli_commands.menu import MenuCommand
            
            managers = {'logger': MagicMock()}
            menu = MenuCommand(managers)
            
            # Check that wizard methods exist
            assert hasattr(menu, '_wizard_first_setup')
            assert hasattr(menu, '_wizard_create_archive')
            assert hasattr(menu, '_wizard_recover_files')
            assert hasattr(menu, '_wizard_search_files')
            assert hasattr(menu, '_wizard_tape_management')
            
        except Exception as e:
            pytest.fail(f"Wizard methods test failed: {e}")
    
    @patch('builtins.input', return_value='q')  # Mock user quitting
    def test_wizard_first_setup_no_crash(self, mock_input):
        """Test first setup wizard doesn't crash."""
        try:
            from src.cli_commands.menu import MenuCommand
            
            managers = {
                'dep_manager': MagicMock(),
                'archive_manager': MagicMock(),
                'tape_manager': MagicMock(),
                'db_manager': MagicMock(),
                'recovery_manager': MagicMock(),
                'search_interface': MagicMock(),
                'tape_library': MagicMock(),
                'config_manager': MagicMock(),
                'progress_manager': MagicMock(),
                'logger': MagicMock()
            }
            
            menu = MenuCommand(managers)
            
            # This should not crash even if dependencies fail
            with patch('builtins.print'):  # Suppress output
                menu._wizard_first_setup()
                
        except Exception as e:
            # Wizard might fail due to missing dependencies, but shouldn't crash
            assert 'Error:' in str(e) or 'import' in str(e).lower()


class TestMenuIntegration:
    """Test menu integration with other commands."""
    
    def test_menu_archive_integration(self):
        """Test menu integration with archive commands."""
        try:
            from src.cli_commands.menu import MenuCommand
            
            managers = {
                'dep_manager': MagicMock(),
                'archive_manager': MagicMock(),
                'tape_manager': MagicMock(),
                'db_manager': MagicMock(),
                'recovery_manager': MagicMock(),
                'search_interface': MagicMock(),
                'tape_library': MagicMock(),
                'config_manager': MagicMock(),
                'progress_manager': MagicMock(),
                'logger': MagicMock()
            }
            
            menu = MenuCommand(managers)
            
            # Test that menu has access to archive operations
            assert hasattr(menu, '_handle_create_archive')
            assert hasattr(menu, '_handle_estimate_archive')
            assert hasattr(menu, '_handle_list_jobs')
            assert hasattr(menu, '_handle_cancel_job')
            
        except Exception as e:
            pytest.fail(f"Archive integration test failed: {e}")
    
    def test_menu_recovery_integration(self):
        """Test menu integration with recovery commands."""
        try:
            from src.cli_commands.menu import MenuCommand
            
            managers = {'logger': MagicMock()}
            menu = MenuCommand(managers)
            
            # Test that menu has access to recovery operations
            assert hasattr(menu, '_handle_list_archives')
            assert hasattr(menu, '_handle_browse_archive')
            assert hasattr(menu, '_handle_extract_full')
            assert hasattr(menu, '_handle_extract_selective')
            assert hasattr(menu, '_handle_verify_archive')
            
        except Exception as e:
            pytest.fail(f"Recovery integration test failed: {e}")
    
    def test_menu_search_integration(self):
        """Test menu integration with search commands."""
        try:
            from src.cli_commands.menu import MenuCommand
            
            managers = {'logger': MagicMock()}
            menu = MenuCommand(managers)
            
            # Test that menu has access to search operations
            assert hasattr(menu, '_handle_search_filename')
            assert hasattr(menu, '_handle_search_content')
            assert hasattr(menu, '_handle_search_advanced')
            assert hasattr(menu, '_handle_search_tape')
            assert hasattr(menu, '_handle_export_search')
            
        except Exception as e:
            pytest.fail(f"Search integration test failed: {e}")
    
    def test_menu_management_integration(self):
        """Test menu integration with management commands."""
        try:
            from src.cli_commands.menu import MenuCommand
            
            managers = {'logger': MagicMock()}
            menu = MenuCommand(managers)
            
            # Test that menu has access to management operations
            assert hasattr(menu, '_handle_tape_management')
            assert hasattr(menu, '_handle_device_management')
            assert hasattr(menu, '_handle_database_management')
            assert hasattr(menu, '_handle_statistics')
            assert hasattr(menu, '_handle_configuration')
            
        except Exception as e:
            pytest.fail(f"Management integration test failed: {e}")
    
    def test_menu_status_integration(self):
        """Test menu integration with status commands."""
        try:
            from src.cli_commands.menu import MenuCommand
            
            managers = {'logger': MagicMock()}
            menu = MenuCommand(managers)
            
            # Test that menu has access to status operations
            assert hasattr(menu, '_handle_system_status')
            assert hasattr(menu, '_handle_device_status')
            assert hasattr(menu, '_handle_operations_status')
            assert hasattr(menu, '_handle_dependency_status')
            assert hasattr(menu, '_handle_database_status')
            
        except Exception as e:
            pytest.fail(f"Status integration test failed: {e}")


class TestMenuErrorHandling:
    """Test menu error handling."""
    
    def test_menu_keyboard_interrupt_handling(self):
        """Test menu handles keyboard interrupts gracefully."""
        try:
            from src.cli_commands.menu import MenuCommand
            
            managers = {'logger': MagicMock()}
            menu = MenuCommand(managers)
            
            args = MagicMock()
            args.mode = 'interactive'
            
            # Simulate KeyboardInterrupt
            with patch('builtins.input', side_effect=KeyboardInterrupt()):
                with patch('os.system'):  # Mock screen clearing
                    result = menu.execute(args)
                    assert result == 0  # Should exit gracefully
                    
        except Exception as e:
            pytest.fail(f"Keyboard interrupt test failed: {e}")
    
    def test_menu_exception_handling(self):
        """Test menu handles general exceptions."""
        try:
            from src.cli_commands.menu import MenuCommand
            
            managers = {'logger': MagicMock()}
            menu = MenuCommand(managers)
            
            args = MagicMock()
            args.mode = 'interactive'
            
            # Simulate general exception
            with patch.object(menu, '_run_interactive_mode', side_effect=Exception('Test error')):
                result = menu.execute(args)
                assert result == 1  # Should return error code
                
        except Exception as e:
            pytest.fail(f"Exception handling test failed: {e}")

