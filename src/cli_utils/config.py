#!/usr/bin/env python3
"""
Configuration Management

Provides configuration file loading and management for the CLI application.
"""

import os
import json
import configparser
from pathlib import Path
from typing import Dict, Any, Optional, Union


class ConfigManager:
    """Manages application configuration from files and environment."""
    
    DEFAULT_CONFIG = {
        'general': {
            'default_device': '',
            'default_compression': True,
            'default_copies': 1,
            'default_mode': 'cached',
            'max_tape_capacity_gb': 6000,  # LTO-7 capacity
            'progress_update_interval': 0.1
        },
        'database': {
            'path': 'data/backupussy.db',
            'backup_interval_days': 7,
            'vacuum_on_startup': False
        },
        'logging': {
            'level': 'INFO',
            'file_rotation': True,
            'max_log_files': 10,
            'max_log_size_mb': 50
        },
        'archive': {
            'temp_dir': '',  # Empty means use system temp
            'verify_checksums': True,
            'index_files_by_default': True,
            'compression_level': 6  # gzip compression level
        },
        'recovery': {
            'verify_by_default': True,
            'preserve_structure_by_default': True,
            'buffer_size_mb': 64
        },
        'search': {
            'default_limit': 1000,
            'case_sensitive': False,
            'use_regex': False
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to custom configuration file
        """
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        self._load_config()
    
    def _get_default_config_paths(self) -> list:
        """Get list of default configuration file paths to check."""
        paths = []
        
        # Current directory
        paths.append(Path.cwd() / 'backupussy.conf')
        paths.append(Path.cwd() / '.backupussy.conf')
        
        # User home directory
        home = Path.home()
        paths.append(home / '.backupussy.conf')
        paths.append(home / '.config' / 'backupussy' / 'config.conf')
        
        # System-wide (Windows)
        if os.name == 'nt':
            appdata = os.environ.get('APPDATA')
            if appdata:
                paths.append(Path(appdata) / 'Backupussy' / 'config.conf')
            
            programdata = os.environ.get('PROGRAMDATA')
            if programdata:
                paths.append(Path(programdata) / 'Backupussy' / 'config.conf')
        
        # System-wide (Unix-like)
        else:
            paths.append(Path('/etc/backupussy/config.conf'))
            paths.append(Path('/usr/local/etc/backupussy/config.conf'))
        
        return paths
    
    def _load_config(self):
        """Load configuration from file."""
        config_paths = []
        
        # If specific config file provided, use only that
        if self.config_file:
            config_paths = [Path(self.config_file)]
        else:
            config_paths = self._get_default_config_paths()
        
        # Find and load the first existing config file
        for config_path in config_paths:
            if config_path.exists() and config_path.is_file():
                try:
                    self._load_config_file(config_path)
                    break
                except Exception as e:
                    # If there's an error loading the config, continue to next file
                    # or use defaults if this was the only/last file
                    if self.config_file:  # If specific file was requested, raise error
                        raise ConfigError(f"Failed to load config file {config_path}: {e}")
                    continue
        
        # Load environment variable overrides
        self._load_env_overrides()
    
    def _load_config_file(self, config_path: Path):
        """Load configuration from a specific file."""
        file_extension = config_path.suffix.lower()
        
        if file_extension == '.json':
            self._load_json_config(config_path)
        elif file_extension in ['.conf', '.ini', '.cfg']:
            self._load_ini_config(config_path)
        else:
            # Try to detect format by content
            with open(config_path, 'r') as f:
                content = f.read().strip()
                if content.startswith('{') and content.endswith('}'):
                    self._load_json_config(config_path)
                else:
                    self._load_ini_config(config_path)
    
    def _load_json_config(self, config_path: Path):
        """Load JSON configuration file."""
        with open(config_path, 'r') as f:
            file_config = json.load(f)
        
        # Deep merge with default config
        self._deep_merge(self.config, file_config)
    
    def _load_ini_config(self, config_path: Path):
        """Load INI-style configuration file."""
        parser = configparser.ConfigParser()
        parser.read(config_path)
        
        # Convert INI format to nested dict
        file_config = {}
        for section_name in parser.sections():
            section = {}
            for key, value in parser.items(section_name):
                # Try to convert values to appropriate types
                section[key] = self._convert_value(value)
            file_config[section_name] = section
        
        # Deep merge with default config
        self._deep_merge(self.config, file_config)
    
    def _convert_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert string value to appropriate type."""
        # Boolean values
        if value.lower() in ('true', 'yes', 'on', '1'):
            return True
        elif value.lower() in ('false', 'no', 'off', '0'):
            return False
        
        # Numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # String value
        return value
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep merge source dict into target dict."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables."""
        prefix = 'BACKUPUSSY_'
        
        for env_key, env_value in os.environ.items():
            if env_key.startswith(prefix):
                # Convert BACKUPUSSY_SECTION_KEY to section.key
                config_key = env_key[len(prefix):].lower()
                
                # Split into section and key
                if '_' in config_key:
                    section, key = config_key.split('_', 1)
                    
                    if section in self.config:
                        # Convert value to appropriate type
                        self.config[section][key] = self._convert_value(env_value)
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        try:
            return self.config[section][key]
        except KeyError:
            return default
    
    def set(self, section: str, key: str, value: Any):
        """Set configuration value."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self.config.get(section, {})
    
    def save(self, config_path: Optional[Path] = None, format: str = 'ini'):
        """Save configuration to file."""
        if config_path is None:
            if self.config_file:
                config_path = Path(self.config_file)
            else:
                # Use default user config location
                config_path = Path.home() / '.config' / 'backupussy' / 'config.conf'
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        else:  # INI format
            parser = configparser.ConfigParser()
            
            for section_name, section_data in self.config.items():
                parser.add_section(section_name)
                for key, value in section_data.items():
                    parser.set(section_name, key, str(value))
            
            with open(config_path, 'w') as f:
                parser.write(f)
    
    def create_sample_config(self, config_path: Path, format: str = 'ini'):
        """Create a sample configuration file with comments."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'ini':
            self._create_sample_ini_config(config_path)
        else:
            self._create_sample_json_config(config_path)
    
    def _create_sample_ini_config(self, config_path: Path):
        """Create a sample INI configuration file."""
        content = """
# Backupussy Configuration File
# This file contains configuration options for the Backupussy LTO backup system.
# All options have sensible defaults, so you only need to uncomment and modify
# the settings you want to change.

[general]
# Default tape device to use when none specified
# default_device = /dev/st0

# Enable compression by default
# default_compression = true

# Default number of tape copies
# default_copies = 1

# Default archive mode (stream or cached)
# default_mode = cached

# Maximum tape capacity in GB (LTO-7 = 6000)
# max_tape_capacity_gb = 6000

# Progress update interval in seconds
# progress_update_interval = 0.1

[database]
# Database file path (relative to application directory)
# path = data/backupussy.db

# How often to backup the database (days)
# backup_interval_days = 7

# Whether to vacuum database on startup
# vacuum_on_startup = false

[logging]
# Logging level (DEBUG, INFO, WARNING, ERROR)
# level = INFO

# Enable log file rotation
# file_rotation = true

# Maximum number of log files to keep
# max_log_files = 10

# Maximum log file size in MB
# max_log_size_mb = 50

[archive]
# Temporary directory for archive creation (empty = system temp)
# temp_dir = 

# Verify checksums during archive creation
# verify_checksums = true

# Index files in database by default
# index_files_by_default = true

# Compression level (1-9, 6 is good balance)
# compression_level = 6

[recovery]
# Verify recovered files by default
# verify_by_default = true

# Preserve directory structure by default
# preserve_structure_by_default = true

# Buffer size for recovery operations (MB)
# buffer_size_mb = 64

[search]
# Default search result limit
# default_limit = 1000

# Case sensitive searches by default
# case_sensitive = false

# Use regular expressions by default
# use_regex = false
"""
        
        with open(config_path, 'w') as f:
            f.write(content.strip())
    
    def _create_sample_json_config(self, config_path: Path):
        """Create a sample JSON configuration file."""
        with open(config_path, 'w') as f:
            json.dump(self.DEFAULT_CONFIG, f, indent=2)
    
    def validate(self) -> list:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate general settings
        general = self.get_section('general')
        if general.get('max_tape_capacity_gb', 0) <= 0:
            errors.append("max_tape_capacity_gb must be positive")
        
        if general.get('default_copies', 1) not in [1, 2]:
            errors.append("default_copies must be 1 or 2")
        
        if general.get('default_mode', 'cached') not in ['stream', 'cached']:
            errors.append("default_mode must be 'stream' or 'cached'")
        
        # Validate archive settings
        archive = self.get_section('archive')
        compression_level = archive.get('compression_level', 6)
        if not isinstance(compression_level, int) or compression_level < 1 or compression_level > 9:
            errors.append("compression_level must be an integer between 1 and 9")
        
        # Validate recovery settings
        recovery = self.get_section('recovery')
        buffer_size = recovery.get('buffer_size_mb', 64)
        if not isinstance(buffer_size, int) or buffer_size < 1:
            errors.append("buffer_size_mb must be a positive integer")
        
        return errors
    
    def get_default_device(self) -> Optional[str]:
        """Get the default tape device."""
        return self.get('general', 'default_device', '/dev/st0')
    
    def get_database_path(self) -> str:
        """Get the database file path."""
        return self.get('database', 'path', 'backupussy.db')
    
    def get_log_level(self) -> str:
        """Get the logging level."""
        return self.get('logging', 'level', 'INFO')
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return json.dumps(self.config, indent=2)


class ConfigError(Exception):
    """Configuration-related error."""
    pass

