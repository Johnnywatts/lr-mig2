#!/usr/bin/env python3
"""
File: scan_cli.py
Purpose: Command-line interface for scanning directories
Version: 1.3.0
Last Updated: 2024-06-13
"""
import argparse
import logging
import sys
import os
from pathlib import Path

from src.logger import setup_logging
from src.file_scanner import FileScanner
from src.config_loader import load_yaml_config, get_target_directories, get_scan_settings
from src.database import db

def load_container_config():
    """Load container configuration from environment or default file."""
    container_config_path = os.environ.get('CONTAINER_CONFIG', 'config/container_config.yaml')
    
    try:
        if os.path.exists(container_config_path):
            with open(container_config_path, 'r') as f:
                import yaml
                config = yaml.safe_load(f)
                return config
        return {}
    except Exception as e:
        print(f"Warning: Failed to load container config: {e}")
        return {}

def main():
    """Main entry point for the CLI."""
    # Load container configuration
    container_config = load_container_config()
    app_config = container_config.get('application', {})
    
    # Set up logging with potential custom level from container config
    log_level = app_config.get('log_level', 'INFO')
    logger = setup_logging()
    logging.getLogger().setLevel(getattr(logging, log_level))
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Scan directories for image files.")
    parser.add_argument(
        "--config", 
        type=str,
        default="config/scan_targets.yaml",
        help="Path to the scan configuration file"
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
    
    # Set log level from command line if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        # But suppress noisy third-party library debug messages
        logging.getLogger('exifread').setLevel(logging.WARNING)
        logging.getLogger('PIL').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    
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
        
        # Suppress interim progress messages
        logging.getLogger('src.file_scanner').setLevel(logging.WARNING)
        
        # Only show important messages
        logger.info("🔥 Starting enhanced file scanner...")
        
        try:
            # Need to scan all valid targets, not just one dir_path
            total_files = 0
            
            for target in valid_targets:
                dir_path = target.get('path')
                logger.info(f"🚀 Scanning: {dir_path}")
                
                scanner = FileScanner(
                    performance_reporting=False,  # Disable verbose progress reports
                    use_db_logging=True
                )
                
                file_count = scanner.scan_directory(dir_path, recursive=recursive)
                total_files += file_count
            
            # Show final summary only
            logger.info("🏁 SCAN COMPLETE!")
            logger.info(f"📁 Total files processed: {total_files:,}")
            
        except Exception as e:
            logger.error(f"❌ Scan failed: {e}")
        
    except Exception as e:
        logger.error(f"Error during scan process: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 