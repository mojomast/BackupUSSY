#!/usr/bin/env python3
"""
LTO Tape Archive Tool
A GUI tool for archiving folders to LTO tape drives using tar and dd.
"""

import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path

# Configure logging
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'archive.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DependencyManager:
    """Manages detection and validation of required external dependencies."""
    
    def __init__(self):
        self.tar_path = None
        self.dd_path = None
        self.mt_path = None
    
    def detect_dependencies(self):
        """Detect tar, dd, and mt executables in PATH or bundled locations."""
        logger.info("Detecting required dependencies...")
        
        # Check for tar (prefer GNU tar from MSYS2)
        self.tar_path = self._find_executable('tar')
        if self.tar_path:
            # Verify it's GNU tar
            try:
                result = subprocess.run([self.tar_path, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if 'GNU tar' in result.stdout:
                    logger.info(f"Found GNU tar at: {self.tar_path}")
                else:
                    logger.warning(f"Found tar but not GNU tar at: {self.tar_path}")
            except Exception as e:
                logger.error(f"Error checking tar version: {e}")
        else:
            logger.error("tar executable not found in PATH")
        
        # Check for dd
        self.dd_path = self._find_executable('dd')
        if self.dd_path:
            logger.info(f"Found dd at: {self.dd_path}")
        else:
            logger.error("dd executable not found in PATH")
        
        # Check for mt (tape control)
        self.mt_path = self._find_executable('mt')
        if self.mt_path:
            logger.info(f"Found mt at: {self.mt_path}")
        else:
            logger.warning("mt executable not found - tape rewinding may not work")
        
        return self.validate_dependencies()
    
    def _find_executable(self, name):
        """Find executable in PATH or bundled locations."""
        # First check PATH
        path = shutil.which(name)
        if path:
            return path
        
        # Check common MSYS2 locations
        msys2_paths = [
            'C:\\msys64\\usr\\bin',
            'C:\\msys32\\usr\\bin',
            os.path.expanduser('~\\msys64\\usr\\bin'),
            os.path.expanduser('~\\msys32\\usr\\bin')
        ]
        
        for msys_path in msys2_paths:
            exe_path = os.path.join(msys_path, f"{name}.exe")
            if os.path.isfile(exe_path):
                return exe_path
        
        # Check bundled location
        bundled_path = os.path.join(os.path.dirname(__file__), '..', 'bin', f"{name}.exe")
        if os.path.isfile(bundled_path):
            return os.path.abspath(bundled_path)
        
        return None
    
    def validate_dependencies(self):
        """Validate that required dependencies are available."""
        missing = []
        
        if not self.tar_path:
            missing.append('tar')
        
        if not self.dd_path:
            missing.append('dd')
        
        if missing:
            logger.error(f"Missing required dependencies: {', '.join(missing)}")
            return False
        
        logger.info("All required dependencies found")
        return True
    
    def get_dependency_info(self):
        """Return information about detected dependencies."""
        return {
            'tar': self.tar_path,
            'dd': self.dd_path,
            'mt': self.mt_path
        }

if __name__ == "__main__":
    # Test dependency detection
    dep_manager = DependencyManager()
    if dep_manager.detect_dependencies():
        print("Dependencies OK:")
        for name, path in dep_manager.get_dependency_info().items():
            print(f"  {name}: {path or 'Not found'}")
    else:
        print("Missing dependencies. Please install MSYS2 or add tar/dd to PATH.")
        sys.exit(1)

