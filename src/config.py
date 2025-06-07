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
EXCLUDED_DIRS = ["*StarQ*"]  # Directories to exclude from scanning 