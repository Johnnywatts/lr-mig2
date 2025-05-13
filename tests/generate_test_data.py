"""
File: generate_test_data.py
Purpose: Create test data for the file scanning functionality
Version: 1.0.0
Last Updated: 2024-06-13
"""
import os
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import logging
import json
import random

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.logger import setup_logging

# Set up logging
logger = setup_logging()

# Define test directory structure
TEST_STRUCTURE = {
    "personal": {
        "2022": {
            "vacation_italy": {
                "files": [
                    {"name": "italy_beach.jpg", "size": 2048},
                    {"name": "italy_sunset.dng", "size": 4096},
                    {"name": "italy_food.jpg", "size": 1536},
                ]
            },
            "family": {
                "files": [
                    {"name": "family_portrait.jpg", "size": 3072},
                    {"name": "kids_playing.dng", "size": 5120},
                ]
            },
            "3StarQ70": {  # This should be excluded
                "files": [
                    {"name": "export1.jpg", "size": 1024},
                    {"name": "export2.jpg", "size": 1024},
                ]
            }
        },
        "2023": {
            "vacation_france": {
                "files": [
                    {"name": "paris.jpg", "size": 2048},
                    {"name": "eiffel_tower.dng", "size": 4096},
                    {"name": "louvre.jpg", "size": 1536},
                ]
            }
        }
    },
    "work": {
        "products": {
            "electronics": {
                "files": [
                    {"name": "phone.dng", "size": 6144},
                    {"name": "laptop.dng", "size": 7168},
                ]
            },
            "2StarQ60": {  # This should be excluded
                "files": [
                    {"name": "export_phone.jpg", "size": 1024},
                    {"name": "export_laptop.jpg", "size": 1024},
                ]
            }
        },
        "clients": {
            "client_a": {
                "files": [
                    {"name": "portrait.jpg", "size": 3072},
                    {"name": "group.dng", "size": 5120},
                ]
            },
            "client_b": {
                "files": [
                    {"name": "event.jpg", "size": 2560},
                    {"name": "conference.dng", "size": 4608},
                ]
            }
        }
    },
    "backup": {
        "old_library": {
            "files": [
                {"name": "old_photo1.jpg", "size": 1024},
                {"name": "old_photo2.dng", "size": 2048},
            ]
        },
        "imports": {
            "camera_a": {
                "files": [
                    {"name": "import1.arw", "size": 8192},
                    {"name": "import2.arw", "size": 8192},
                ]
            },
            "camera_b": {
                "files": [
                    {"name": "import1.cr2", "size": 7680},
                    {"name": "import2.cr2", "size": 7680},
                ]
            }
        }
    }
}

# Create fake exif data for test files
def create_fake_exif(file_path, file_type):
    """Create fake EXIF data for a test file based on its type."""
    if file_type.lower() in ['.jpg', '.jpeg']:
        exif = {
            "Make": "Test Camera",
            "Model": "Test Model",
            "DateTime": datetime.now().strftime("%Y:%m:%d %H:%M:%S"),
            "ExposureTime": "1/100",
            "FNumber": "5.6",
            "ISO": "100",
            "FocalLength": "50mm"
        }
    elif file_type.lower() in ['.dng', '.arw', '.cr2']:
        exif = {
            "Make": "Pro Camera",
            "Model": "Pro Model",
            "DateTime": datetime.now().strftime("%Y:%m:%d %H:%M:%S"),
            "ExposureTime": "1/250",
            "FNumber": "2.8",
            "ISO": "200",
            "FocalLength": "85mm"
        }
    else:
        exif = {}
    
    # Save fake exif as a JSON file alongside the test file
    exif_path = f"{file_path}.exif.json"
    with open(exif_path, 'w') as f:
        json.dump(exif, f, indent=2)
    
    return exif

def create_directory_structure(base_dir, structure, current_path=""):
    """Recursively create a directory structure based on the provided structure."""
    for name, content in structure.items():
        if name == "files":
            # Create files
            for file_info in content:
                file_name = file_info["name"]
                file_size = file_info["size"]
                file_path = os.path.join(base_dir, current_path, file_name)
                
                # Create file with random content of specified size
                with open(file_path, 'wb') as f:
                    f.write(os.urandom(file_size))
                
                # Create fake exif data
                file_ext = os.path.splitext(file_name)[1]
                create_fake_exif(file_path, file_ext)
                
                logger.info(f"Created file: {file_path} ({file_size} bytes)")
        else:
            # Create directory and recurse
            dir_path = os.path.join(base_dir, current_path, name)
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            
            new_path = os.path.join(current_path, name) if current_path else name
            create_directory_structure(base_dir, content, new_path)

def main():
    """Main function to create test data."""
    parser = argparse.ArgumentParser(description="Generate test data for file scanning.")
    parser.add_argument(
        "--dir", 
        type=str, 
        default=os.path.join(os.path.dirname(__file__), "test_data"),
        help="Directory to create test data in (default: ./test_data)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean (remove) the test data directory if it exists"
    )
    
    args = parser.parse_args()
    
    # Create or clean the test directory
    test_dir = args.dir
    if os.path.exists(test_dir):
        if args.clean:
            logger.info(f"Cleaning existing test directory: {test_dir}")
            shutil.rmtree(test_dir)
        else:
            logger.error(f"Test directory already exists: {test_dir}")
            logger.error("Use --clean to remove it or specify a different directory with --dir")
            return 1
    
    # Create the base test directory
    os.makedirs(test_dir, exist_ok=True)
    logger.info(f"Creating test data in: {test_dir}")
    
    # Create the directory structure
    create_directory_structure(test_dir, TEST_STRUCTURE)
    
    # Print summary
    total_files = sum(1 for _, struct in TEST_STRUCTURE.items() 
                     for item in _find_all_files(struct))
    
    logger.info("Test data creation complete:")
    logger.info(f"- Created {total_files} test files")
    logger.info(f"- Test data directory: {test_dir}")
    logger.info("")
    logger.info("To scan this test data, run:")
    logger.info(f"./docker/scan.sh --scan-config config/scan_targets_testing.yaml --verbose")
    
    return 0

def _find_all_files(structure, current_path=""):
    """Helper function to find all files in the structure recursively."""
    for name, content in structure.items():
        if name == "files":
            for file_info in content:
                yield file_info
        else:
            new_path = os.path.join(current_path, name) if current_path else name
            yield from _find_all_files(content, new_path)

if __name__ == "__main__":
    sys.exit(main()) 