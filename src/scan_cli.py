#!/usr/bin/env python3
"""
File: scan_cli.py
Purpose: Command-line interface for scanning directories
Version: 1.2.0
Last Updated: 2024-06-13
"""
import argparse
import logging
import sys
import os
from pathlib import Path

from src.logger import setup_logging
from src.file_scanner import scanner
from src.config_loader import load_yaml_config, get_target_directories, get_scan_settings
from src.database import db

def main():
    """Main entry point for the CLI."""
    # Set up logging
    logger = setup_logging()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Scan directories for image files.")
    parser.add_argument(
        "--config", 
        type=str,
        default="config/scan_targets.yaml",
        help="Path to the YAML configuration file"
    )
    parser.add_argument(
        "--group", 
        type=str,
        help="Only scan directories from this group (e.g., 'personal', 'work')"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )
    parser.add_argument(
        "--test", 
        action="store_true", 
        help="Test run - verify paths but don't scan files"
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Test database connection
    if not db.test_connection():
        logger.error("Failed to connect to database. Please check database configuration.")
        sys.exit(1)
    
    # Check if config file exists
    config_path = args.config
    try:
        logger.info(f"Loading configuration from {config_path}")
        config = load_yaml_config(config_path)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Get all directories to scan
    try:
        all_targets = get_target_directories(config)
        scan_settings = get_scan_settings(config)
        
        # Filter by group if specified
        if args.group:
            targets = [t for t in all_targets if t.get('group') == args.group]
            if not targets:
                logger.error(f"No directories found for group: {args.group}")
                sys.exit(1)
            logger.info(f"Filtered to {len(targets)} directories in group '{args.group}'")
        else:
            targets = all_targets
            logger.info(f"Found {len(targets)} directories to scan across all groups")
        
        # Get scan settings
        recursive = scan_settings.get('recursive', True)
        
        # Check if directories exist
        valid_targets = []
        for target in targets:
            dir_path = target.get('path')
            description = target.get('description', '')
            
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                valid_targets.append(target)
                logger.info(f"Verified directory: {dir_path} ({description})")
            else:
                logger.warning(f"Directory not found, will be skipped: {dir_path}")
        
        if not valid_targets:
            logger.error("No valid directories found to scan!")
            sys.exit(1)
        
        # Exit if this is just a test run
        if args.test:
            logger.info("Test completed successfully. Found valid directories to scan.")
            sys.exit(0)
        
        # Process each directory
        total_files = 0
        for target in valid_targets:
            dir_path = target.get('path')
            description = target.get('description', '')
            category = target.get('category')
            
            logger.info(f"Scanning directory: {dir_path} ({description})")
            if category:
                logger.info(f"Category: {category}")
            
            # Scan the directory
            file_count = scanner.scan_directory(dir_path, recursive=recursive)
            total_files += file_count
            
            logger.info(f"Completed scanning {dir_path}. Processed {file_count} files.")
        
        logger.info(f"All scans complete. Total files processed: {total_files}")
        
    except Exception as e:
        logger.error(f"Error during scan process: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 