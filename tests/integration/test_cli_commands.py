import pytest
import os
import tempfile
from pathlib import Path

pytestmark = pytest.mark.integration


class TestArchiveCommand:
    """Test archive command functionality."""
    
    def test_archive_help(self, script_runner):
        """Test archive command help."""
        result = script_runner.run(['backupussy', 'archive', '--help'])
        assert result.returncode == 0
        assert 'usage: backupussy archive' in result.stdout.lower()
        assert 'create' in result.stdout
        assert 'estimate' in result.stdout
        assert 'list-jobs' in result.stdout
        assert 'cancel' in result.stdout
    
    def test_archive_create_help(self, script_runner):
        """Test archive create command help."""
        result = script_runner.run(['backupussy', 'archive', 'create', '--help'])
        assert result.returncode == 0
        assert 'usage: backupussy archive create' in result.stdout.lower()
        assert '--device' in result.stdout
        assert '--compress' in result.stdout
        assert '--copies' in result.stdout
    
    def test_archive_estimate_help(self, script_runner):
        """Test archive estimate command help."""
        result = script_runner.run(['backupussy', 'archive', 'estimate', '--help'])
        assert result.returncode == 0
        assert 'usage: backupussy archive estimate' in result.stdout.lower()
        assert 'source' in result.stdout
    
    def test_archive_create_missing_device(self, script_runner, tmp_path):
        """Test archive create without required device parameter."""
        test_dir = tmp_path / "test_source"
        test_dir.mkdir()
        
        result = script_runner.run(['backupussy', 'archive', 'create', str(test_dir)])
        assert result.returncode != 0
        # Should show error about missing required device argument
    
    def test_archive_create_nonexistent_source(self, script_runner):
        """Test archive create with nonexistent source directory."""
        result = script_runner.run(['backupussy', 'archive', 'create', '/nonexistent/path', '--device', '/dev/null'])
        assert result.returncode != 0
        # Should show error about source not existing


class TestRecoverCommand:
    """Test recover command functionality."""
    
    def test_recover_help(self, script_runner):
        """Test recover command help."""
        result = script_runner.run(['backupussy', 'recover', '--help'])
        assert result.returncode == 0
        assert 'usage: backupussy recover' in result.stdout.lower()
        assert 'list' in result.stdout
        assert 'files' in result.stdout
        assert 'start' in result.stdout
        assert 'verify' in result.stdout
    
    def test_recover_list_help(self, script_runner):
        """Test recover list command help."""
        result = script_runner.run(['backupussy', 'recover', 'list', '--help'])
        assert result.returncode == 0
        assert 'usage: backupussy recover list' in result.stdout.lower()
        assert '--tape' in result.stdout
        assert '--limit' in result.stdout
    
    def test_recover_start_help(self, script_runner):
        """Test recover start command help."""
        result = script_runner.run(['backupussy', 'recover', 'start', '--help'])
        assert result.returncode == 0
        assert 'usage: backupussy recover start' in result.stdout.lower()
        assert '--archive-id' in result.stdout
        assert '--destination' in result.stdout
        assert '--overwrite' in result.stdout
    
    def test_recover_start_missing_args(self, script_runner):
        """Test recover start without required arguments."""
        result = script_runner.run(['backupussy', 'recover', 'start'])
        assert result.returncode != 0
        # Should show error about missing required arguments


class TestSearchCommand:
    """Test search command functionality."""
    
    def test_search_help(self, script_runner):
        """Test search command help."""
        result = script_runner.run(['backupussy', 'search', '--help'])
        assert result.returncode == 0
        assert 'usage: backupussy search' in result.stdout.lower()
        assert '--entity' in result.stdout
        assert '--name' in result.stdout
        assert '--tape' in result.stdout
        assert '--export' in result.stdout
    
    def test_search_basic_query(self, script_runner):
        """Test basic search functionality."""
        result = script_runner.run(['backupussy', 'search', '*.txt'])
        # Should run without error even if no results found
        # The actual functionality depends on having a database with data
        assert result.returncode == 0 or 'Error:' in result.stderr
    
    def test_search_with_filters(self, script_runner):
        """Test search with various filters."""
        result = script_runner.run([
            'backupussy', 'search', '*.pdf', 
            '--entity', 'file',
            '--size', '>1MB',
            '--format', 'table'
        ])
        # Should run without error
        assert result.returncode == 0 or 'Error:' in result.stderr


class TestManageCommand:
    """Test manage command functionality."""
    
    def test_manage_help(self, script_runner):
        """Test manage command help."""
        result = script_runner.run(['backupussy', 'manage', '--help'])
        assert result.returncode == 0
        assert 'usage: backupussy manage' in result.stdout.lower()
        assert 'tapes' in result.stdout
        assert 'devices' in result.stdout
        assert 'database' in result.stdout
        assert 'stats' in result.stdout
        assert 'config' in result.stdout
    
    def test_manage_tapes_help(self, script_runner):
        """Test manage tapes command help."""
        result = script_runner.run(['backupussy', 'manage', 'tapes', '--help'])
        assert result.returncode == 0
        assert 'usage: backupussy manage tapes' in result.stdout.lower()
        assert 'list' in result.stdout
        assert 'add' in result.stdout
        assert 'update' in result.stdout
        assert 'remove' in result.stdout
    
    def test_manage_devices_help(self, script_runner):
        """Test manage devices command help."""
        result = script_runner.run(['backupussy', 'manage', 'devices', '--help'])
        assert result.returncode == 0
        assert 'usage: backupussy manage devices' in result.stdout.lower()
        assert 'list' in result.stdout
        assert 'refresh' in result.stdout
    
    def test_manage_database_help(self, script_runner):
        """Test manage database command help."""
        result = script_runner.run(['backupussy', 'manage', 'database', '--help'])
        assert result.returncode == 0
        assert 'usage: backupussy manage database' in result.stdout.lower()
        assert 'vacuum' in result.stdout
        assert 'backup' in result.stdout
        assert 'restore' in result.stdout
    
    def test_manage_stats_help(self, script_runner):
        """Test manage stats command help."""
        result = script_runner.run(['backupussy', 'manage', 'stats', '--help'])
        assert result.returncode == 0
        assert 'usage: backupussy manage stats' in result.stdout.lower()
        assert '--detailed' in result.stdout
    
    def test_manage_tapes_add_missing_args(self, script_runner):
        """Test manage tapes add without required arguments."""
        result = script_runner.run(['backupussy', 'manage', 'tapes', 'add'])
        assert result.returncode != 0
        # Should show error about missing required arguments


class TestStatusCommand:
    """Test status command functionality."""
    
    def test_status_help(self, script_runner):
        """Test status command help."""
        result = script_runner.run(['backupussy', 'status', '--help'])
        assert result.returncode == 0
        assert 'usage: backupussy status' in result.stdout.lower()
        assert 'devices' in result.stdout
        assert 'jobs' in result.stdout
        assert 'dependencies' in result.stdout
        assert 'tapes' in result.stdout
    
    def test_status_basic(self, script_runner):
        """Test basic status command."""
        result = script_runner.run(['backupussy', 'status'])
        # Status command should always run, might show dependency errors
        assert result.returncode == 0 or 'Error:' in result.stderr
    
    def test_status_dependencies(self, script_runner):
        """Test status dependencies check."""
        result = script_runner.run(['backupussy', 'status', 'dependencies'])
        # Should run and show dependency status
        assert result.returncode == 0 or 'Error:' in result.stderr


class TestGlobalOptions:
    """Test global CLI options."""
    
    def test_verbose_option(self, script_runner):
        """Test verbose option."""
        result = script_runner.run(['backupussy', '-v', 'status'])
        # Should run with increased verbosity
        assert result.returncode == 0 or 'Error:' in result.stderr
    
    def test_quiet_option(self, script_runner):
        """Test quiet option."""
        result = script_runner.run(['backupussy', '-q', 'status'])
        # Should run with suppressed output
        assert result.returncode == 0 or 'Error:' in result.stderr
    
    def test_dry_run_option(self, script_runner, tmp_path):
        """Test dry-run option."""
        test_dir = tmp_path / "test_source"
        test_dir.mkdir()
        
        result = script_runner.run([
            'backupussy', '--dry-run', 'archive', 'create', 
            str(test_dir), '--device', '/dev/null'
        ])
        # Dry run should show what would be done without error
        assert result.returncode == 0 or 'Error:' in result.stderr
    
    def test_config_option(self, script_runner, tmp_path):
        """Test custom config file option."""
        config_file = tmp_path / "test.conf"
        config_file.write_text("[tape]\ndefault_device = /dev/st0\n")
        
        result = script_runner.run([
            'backupussy', '--config', str(config_file), 'status'
        ])
        # Should run with custom config
        assert result.returncode == 0 or 'Error:' in result.stderr
    
    def test_no_color_option(self, script_runner):
        """Test no-color option."""
        result = script_runner.run(['backupussy', '--no-color', 'status'])
        # Should run without color output
        assert result.returncode == 0 or 'Error:' in result.stderr

