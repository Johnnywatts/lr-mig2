#!/usr/bin/env python3
"""
File: scan_cli.py
Purpose: Command-line interface for scanning directories
Version: 1.0.0
Last Updated: 2024-06-13
"""
import argparse
import logging
import sys
from pathlib import Path

from src.logger import setup_logging
from src.file_scanner import scanner

def main():
    """Main entry point for the CLI."""
    # Set up logging
    logger = setup_logging()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Scan directories for image files.")
    parser.add_argument(
        "directory", 
        type=str, 
        help="Directory to scan"
    )
    parser.add_argument(
        "--no-recursive", 
        action="store_false", 
        dest="recursive",
        help="Disable recursive scanning"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Check if directory exists
    scan_dir = Path(args.directory)
    if not scan_dir.exists() or not scan_dir.is_dir():
        logger.error(f"Directory not found: {args.directory}")
        sys.exit(1)
    
    # Scan directory
    try:
        file_count = scanner.scan_directory(args.directory, args.recursive)
        print(f"Scan complete. Processed {file_count} files.")
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 