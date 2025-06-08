"""
Configuration management for the application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TEST_DATA_DIR = PROJECT_ROOT / "tests" / "test_data"

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "lrmig2")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# File scanning configuration
SUPPORTED_RAW_FORMATS = [
    # RAW formats (without leading dots for comparison)
    "dng", "arw", "cr2", "cr3", "nef", "raf", "orf", "rw2", "srw", "x3f",
    # JPEG formats
    "jpg", "jpeg", 
    # TIFF formats
    "tif", "tiff",
    # Other formats
    "png", "bmp"
]

# Enhanced exclusion patterns for Windows system directories and other problematic folders
EXCLUDED_DIRS = [
    "*StarQ*",                    # Lightroom export directories
    "$RECYCLE.BIN*",             # Windows recycle bin
    "System Volume Information*", # Windows system directory
    "RECYCLER*",                 # Older Windows recycle bin
    ".Trash*",                   # macOS trash
    ".DS_Store*",                # macOS metadata
    "Thumbs.db*",                # Windows thumbnails
    "desktop.ini*",              # Windows desktop settings
    ".git*",                     # Git directories
    "__pycache__*",              # Python cache
    "node_modules*",             # Node.js modules
    ".svn*",                     # Subversion
    ".hg*"                       # Mercurial
] 