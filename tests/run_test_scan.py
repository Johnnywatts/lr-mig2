"""
File: run_test_scan.py
Purpose: Run a test scan on the generated test data
Version: 1.0.0
Last Updated: 2024-06-13
"""
import os
import sys
import argparse
import logging
from pathlib import Path
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.logger import setup_logging
from src.database import db
from src.file_scanner import scanner
from src.config_loader import load_yaml_config, get_target_directories, get_scan_settings

def main():
    """Run a test scan on generated test data."""
    # Set up logging
    logger = setup_logging()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run a test scan.")
    parser.add_argument(
        "--config", 
        type=str,
        default=os.path.join(os.path.dirname(__file__), "config", "test_scan_targets.yaml"),
        help="Path to the test configuration file"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )
    parser.add_argument(
        "--group", 
        type=str,
        help="Only scan directories from this group (e.g., 'personal', 'work')"
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Test database connection
    if not db.test_connection():
        logger.error("Failed to connect to database. Please check configuration.")
        sys.exit(1)
    
    # Load configuration
    try:
        config_path = args.config
        logger.info(f"Loading configuration from {config_path}")
        config = load_yaml_config(config_path)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Get directories to scan
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
        
        # Process each directory
        total_files = 0
        for target in targets:
            dir_path = target.get('path')
            description = target.get('description', '')
            category = target.get('category')
            
            if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                logger.warning(f"Directory not found, skipping: {dir_path}")
                continue
                
            logger.info(f"Scanning directory: {dir_path} ({description})")
            if category:
                logger.info(f"Category: {category}")
            
            # Scan the directory
            file_count = scanner.scan_directory(dir_path, recursive=recursive)
            total_files += file_count
            
            logger.info(f"Completed scanning {dir_path}. Processed {file_count} files.")
        
        logger.info(f"All scans complete. Total files processed: {total_files}")
        
        # Query and display database stats
        with db.get_cursor() as cur:
            # Count files by extension
            cur.execute("""
                SELECT 
                    SUBSTRING(filename FROM '\\.[^.]*$') as extension,
                    COUNT(*) as count
                FROM files
                GROUP BY extension
                ORDER BY count DESC
            """)
            results = cur.fetchall()
            
            logger.info("\nFiles by extension:")
            for result in results:
                logger.info(f"  - {result['extension']}: {result['count']} files")
            
            # Count directories by category
            cur.execute("""
                SELECT 
                    category,
                    COUNT(*) as count
                FROM directories
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
            """)
            results = cur.fetchall()
            
            logger.info("\nDirectories by category:")
            for result in results:
                cat = result['category'] if result['category'] else 'Unassigned'
                logger.info(f"  - {cat}: {result['count']} directories")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during test scan: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main()) 