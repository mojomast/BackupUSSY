#!/usr/bin/env python3
"""
BackupUSSY - Professional LTO Tape Archive Tool
Minimal GUI for packaging
"""

import os
import sys
import logging

try:
    import FreeSimpleGUI as sg
except ImportError:
    print("FreeSimpleGUI not installed. Please run: pip install FreeSimpleGUI")
    sys.exit(1)

from version import *

# Configure FreeSimpleGUI theme
sg.theme('DarkBlue3')

logger = logging.getLogger(__name__)

class LTOArchiveGUI:
    """Main GUI application for LTO tape archiving."""
    
    def __init__(self):
        self.window = None
        self.setup_logging()
        self.create_gui()
    
    def setup_logging(self):
        """Setup basic logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def create_gui(self):
        """Create the main GUI window."""
        layout = [
            [sg.Text(f'BackupUSSY v{APP_VERSION}', font=('Arial', 16, 'bold'))],
            [sg.Text('Professional LTO Tape Archive Tool')],
            [sg.HSeparator()],
            [sg.Text('This is a minimal version for packaging.')],
            [sg.Text('Full functionality requires proper initialization.')],
            [sg.HSeparator()],
            [sg.Button('Close', key='-CLOSE-')]
        ]
        
        self.window = sg.Window(
            f'BackupUSSY v{APP_VERSION}',
            layout,
            size=(400, 200),
            resizable=False,
            finalize=True
        )
    
    def run(self):
        """Main GUI event loop."""
        while True:
            event, values = self.window.read()
            
            if event in (sg.WIN_CLOSED, '-CLOSE-'):
                break
        
        self.window.close()

def main():
    """Main entry point."""
    try:
        app = LTOArchiveGUI()
        app.run()
    except Exception as e:
        sg.popup_error('Error', f'Application failed to start: {e}')
        logging.error(f"Fatal error: {e}")

if __name__ == '__main__':
    main()

