"""
Custom Exceptions for Backupussy

This module defines custom exception classes for the application to allow for more
specific error handling and clearer error messages.
"""

class BackupussyError(Exception):
    """Base class for all application-specific errors."""
    pass

class DependencyError(BackupussyError):
    """Raised when a required external dependency is not found."""
    pass

class ConfigError(BackupussyError):
    """Raised for errors related to configuration file loading or validation."""
    pass

class DatabaseError(BackupussyError):
    """Raised for errors related to database operations."""
    pass

class TapeError(BackupussyError):
    """Raised for errors related to tape drive operations (e.g., mt, dd)."""
    pass

class ArchiveError(BackupussyError):
    """Raised for errors occurring during the archiving process (e.g., tar)."""
    pass

class RecoveryError(BackupussyError):
    """Raised for errors occurring during the recovery process."""
    pass

class SearchError(BackupussyError):
    """Raised for errors related to search operations."""
    pass

class ValidationError(BackupussyError):
    """Raised when user input or data validation fails."""
    pass

class ManagementError(BackupussyError):
    """Raised for errors related to system management operations."""
    pass
