import pytest

pytestmark = pytest.mark.integration

def test_backupussy_help(script_runner):
    """Test that `backupussy --help` runs successfully and shows usage."""
    result = script_runner.run(['backupussy', '--help'])
    assert result.returncode == 0
    assert result.stdout is not None
    assert 'usage: backupussy' in result.stdout.lower()
    assert 'LTO Tape Backup System - Terminal Interface' in result.stdout
    # Check for a few common commands in help text
    assert 'archive' in result.stdout
    assert 'recover' in result.stdout
    assert 'manage' in result.stdout
    assert 'status' in result.stdout

def test_backupussy_version(script_runner):
    """Test that `backupussy --version` runs successfully and shows version."""
    result = script_runner.run(['backupussy', '--version'])
    assert result.returncode == 0
    assert result.stdout is not None
    assert 'backupussy 1.0' in result.stdout.lower() # Version is hardcoded in cli.py


def test_backupussy_manage_help(script_runner):
    """Test that `backupussy manage --help` runs successfully."""
    result = script_runner.run(['backupussy', 'manage', '--help'])
    assert result.returncode == 0
    assert result.stdout is not None
    assert 'usage: backupussy manage' in result.stdout.lower()
    assert 'tapes' in result.stdout
    assert 'devices' in result.stdout
    assert 'config' in result.stdout # Check for the newly added config command


def test_backupussy_manage_config_generate_help(script_runner):
    """Test `backupussy manage config generate --help`."""
    result = script_runner.run(['backupussy', 'manage', 'config', 'generate', '--help'])
    assert result.returncode == 0
    assert result.stdout is not None
    assert 'usage: backupussy manage config generate' in result.stdout.lower()
    assert '--path' in result.stdout
    assert '--force' in result.stdout

def test_backupussy_manage_config_generate_creates_file(script_runner, tmp_path):
    """Test that `backupussy manage config generate --path <path>` creates a file."""
    config_file = tmp_path / "generated.conf"
    result = script_runner.run(['backupussy', 'manage', 'config', 'generate', '--path', str(config_file)])

    assert result.returncode == 0
    assert "Sample configuration file generated at" in result.stdout
    assert str(config_file) in result.stdout
    assert config_file.exists()
    assert config_file.is_file()
    assert config_file.stat().st_size > 0 # Check that the file is not empty

    # Test --force option
    result_force = script_runner.run(['backupussy', 'manage', 'config', 'generate', '--path', str(config_file), '--force'])
    assert result_force.returncode == 0
    assert "Sample configuration file generated at" in result_force.stdout # Ensure it still reports success
    assert config_file.exists() # File should still exist

    # Test without --force when file exists (should fail or prompt, but CLI exits with error)
    # For this CLI, it exits with an error if the file exists and --force is not used.
    result_no_force_exists = script_runner.run(['backupussy', 'manage', 'config', 'generate', '--path', str(config_file)])
    assert result_no_force_exists.returncode != 0 # Should be non-zero for error
    assert "Error: Configuration file already exists" in result_no_force_exists.stderr
    assert "Use --force to overwrite." in result_no_force_exists.stderr
