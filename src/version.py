#!/usr/bin/env python3
"""
BackupUSSY Version Information
"""

# Application Information
APP_NAME = "BackupUSSY"
APP_VERSION = "0.1.5"
APP_DESCRIPTION = "Professional LTO Tape Archive Tool"
APP_AUTHOR = "Kyle Durepos"
APP_COPYRIGHT = "© 2025 Kyle Durepos"
APP_WEBSITE = "https://github.com/mojomast/backupussy"

# Build Information
APP_BUILD = "20250610"
APP_CODENAME = "Critical GUI Fixes"

# Full version string
FULL_VERSION = f"{APP_NAME} v{APP_VERSION} ({APP_CODENAME})"
SHORT_VERSION = f"{APP_NAME} v{APP_VERSION}"

# Window titles
MAIN_WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION} - {APP_DESCRIPTION}"
BROWSER_WINDOW_TITLE = f"{APP_NAME} Tape Browser"
SEARCH_WINDOW_TITLE = f"{APP_NAME} Search & Recovery"
ADVANCED_SEARCH_TITLE = f"{APP_NAME} Advanced Search"

# Status messages
READY_MESSAGE = f"{APP_NAME} ready"
INIT_MESSAGE = f"{APP_NAME} {APP_VERSION} initialized successfully"

def get_version_info():
    """Get comprehensive version information."""
    return {
        'name': APP_NAME,
        'version': APP_VERSION,
        'build': APP_BUILD,
        'description': APP_DESCRIPTION,
        'author': APP_AUTHOR,
        'copyright': APP_COPYRIGHT,
        'website': APP_WEBSITE,
        'codename': APP_CODENAME,
        'full_version': FULL_VERSION
    }

def get_about_text():
    """Get formatted about text."""
    return f"""{FULL_VERSION}
{APP_DESCRIPTION}

{APP_COPYRIGHT}

A professional-grade LTO tape archiving solution with
advanced search, recovery, and library management capabilities.

Built with FreeSimpleGUI and designed for reliability.

For more information, visit:
{APP_WEBSITE}"""

if __name__ == '__main__':
    print(FULL_VERSION)
    print(get_about_text())

