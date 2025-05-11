"""
Logging configuration for the application.
"""
import logging
import os
from pathlib import Path
import subprocess
from datetime import datetime
import sys

def get_git_info():
    """Get current git commit information."""
    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
        commit_date = subprocess.check_output(['git', 'log', '-1', '--format=%cd']).decode('ascii').strip()
        return f"commit:{commit_hash} date:{commit_date}"
    except:
        return "no-git-info"

def setup_logging():
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Get current date for log file naming
    current_date = datetime.now().strftime("%Y-%m-%d")
    git_info = get_git_info()
    
    # Debug information
    print(f"Log directory: {log_dir.absolute()}", file=sys.stderr)
    print(f"Log directory exists: {log_dir.exists()}", file=sys.stderr)
    print(f"Log directory is writable: {os.access(log_dir, os.W_OK)}", file=sys.stderr)
    
    # Configure logging with force=True to ensure it's set up
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / f"app_{current_date}_{git_info}.log", mode='a'),
            logging.StreamHandler()
        ],
        force=True
    )
    
    # Set up test logging with force=True
    test_logger = logging.getLogger('tests')
    test_logger.setLevel(logging.INFO)
    test_logger.addHandler(logging.FileHandler(log_dir / f"tests_{current_date}_{git_info}.log", mode='a'))
    
    # Force an initial log message
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    test_logger.info("Test logging system initialized")
    
    return logger 