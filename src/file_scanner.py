"""
File: file_scanner.py
Purpose: Scans directories for image files and extracts metadata
Version: 1.0.0
Last Updated: 2024-06-13
"""
import os
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
import fnmatch
import exifread
from PIL import Image

from src.config import SUPPORTED_RAW_FORMATS, EXCLUDED_DIRS
from src.database import db

# Set up logging
logger = logging.getLogger(__name__)

class FileScanner:
    """Scans directories for image files and extracts metadata."""
    
    def __init__(self):
        """Initialize the file scanner."""
        self.supported_extensions = set(SUPPORTED_RAW_FORMATS + ['.jpg', '.jpeg'])
        self.excluded_patterns = EXCLUDED_DIRS
        
    def is_excluded_dir(self, dirpath: str) -> bool:
        """Check if directory should be excluded based on patterns.
        
        Args:
            dirpath: Directory path to check
            
        Returns:
            bool: True if directory should be excluded, False otherwise
        """
        dir_name = os.path.basename(dirpath)
        return any(fnmatch.fnmatch(dir_name, pattern) for pattern in self.excluded_patterns)
    
    def scan_directory(self, root_dir: str, recursive: bool = True) -> int:
        """Scan a directory for image files and store metadata.
        
        Args:
            root_dir: Root directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            int: Number of files processed
        """
        root_path = Path(root_dir)
        if not root_path.exists() or not root_path.is_dir():
            logger.error(f"Directory not found or not a directory: {root_dir}")
            return 0
        
        logger.info(f"Starting scan of directory: {root_dir}")
        
        # Store top-level directory
        self._store_directory(str(root_path), None)
        
        # Keep track of directories already in DB
        processed_dirs = set()
        processed_dirs.add(str(root_path))
        
        # Count files processed
        file_count = 0
        
        # Walk through directory
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Skip excluded directories
            if self.is_excluded_dir(dirpath):
                logger.debug(f"Skipping excluded directory: {dirpath}")
                dirnames.clear()  # This prevents os.walk from recursing into this dir
                continue
            
            # Store directory info if it's a subdirectory
            dir_path_obj = Path(dirpath)
            if dirpath != root_dir:
                parent_path = str(dir_path_obj.parent)
                if parent_path in processed_dirs:
                    self._store_directory(dirpath, parent_path)
                    processed_dirs.add(dirpath)
            
            # Process files
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if self._process_file(file_path):
                    file_count += 1
            
            # Stop recursion if not requested
            if not recursive:
                break
        
        logger.info(f"Completed scanning {root_dir}. Processed {file_count} files")
        return file_count
    
    def _process_file(self, file_path: str) -> bool:
        """Process a single file, extracting metadata and storing in DB.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if file was processed, False otherwise
        """
        path_obj = Path(file_path)
        
        # Skip if not a supported file type
        if path_obj.suffix.lower() not in self.supported_extensions:
            return False
        
        try:
            # Get file stats
            file_stats = path_obj.stat()
            file_size = file_stats.st_size
            created_date = datetime.fromtimestamp(file_stats.st_ctime)
            modified_date = datetime.fromtimestamp(file_stats.st_mtime)
            
            # Extract EXIF data
            exif_data = self._extract_exif(file_path)
            
            # Store in database
            self._store_file(
                path_obj.name,
                str(path_obj.parent),
                file_path,
                file_size,
                created_date,
                modified_date,
                exif_data
            )
            
            logger.debug(f"Processed file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return False
    
    def _extract_exif(self, file_path: str) -> Dict[str, Any]:
        """Extract EXIF data from image file.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dict[str, Any]: Dictionary of EXIF metadata
        """
        exif_data = {}
        
        try:
            # For RAW files
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                # Convert exifread tags to serializable dictionary
                for tag, value in tags.items():
                    exif_data[tag] = str(value)
                    
            # Try to get additional data with PIL for JPEGs
            if file_path.lower().endswith(('.jpg', '.jpeg')):
                with Image.open(file_path) as img:
                    if hasattr(img, '_getexif') and img._getexif():
                        pil_exif = img._getexif()
                        for tag_id, value in pil_exif.items():
                            # Skip binary data
                            if isinstance(value, bytes):
                                continue
                            # Convert values to strings to ensure they're serializable
                            if hasattr(value, '__str__'):
                                exif_data[f"PIL_{tag_id}"] = str(value)
        
        except Exception as e:
            logger.warning(f"Error extracting EXIF data from {file_path}: {e}")
        
        return exif_data
    
    def _store_directory(self, dir_path: str, parent_path: Optional[str]) -> int:
        """Store directory information in the database.
        
        Args:
            dir_path: Directory path
            parent_path: Parent directory path or None if root
            
        Returns:
            int: Directory ID in database
        """
        try:
            with db.get_cursor() as cur:
                # Check if directory already exists
                cur.execute(
                    "SELECT id FROM directories WHERE dirpath = %s",
                    (dir_path,)
                )
                result = cur.fetchone()
                
                if result:
                    return result['id']
                
                # Get parent ID if available
                parent_id = None
                if parent_path:
                    cur.execute(
                        "SELECT id FROM directories WHERE dirpath = %s",
                        (parent_path,)
                    )
                    parent_result = cur.fetchone()
                    if parent_result:
                        parent_id = parent_result['id']
                
                # Insert directory
                cur.execute(
                    """
                    INSERT INTO directories 
                    (dirpath, parent_id) 
                    VALUES (%s, %s) 
                    RETURNING id
                    """,
                    (dir_path, parent_id)
                )
                return cur.fetchone()['id']
                
        except Exception as e:
            logger.error(f"Error storing directory {dir_path}: {e}")
            return None
    
    def _store_file(
        self, 
        filename: str, 
        dir_path: str, 
        filepath: str,
        filesize: int, 
        created_date: datetime, 
        modified_date: datetime, 
        exif_data: Dict[str, Any]
    ) -> int:
        """Store file metadata in the database.
        
        Args:
            filename: File name
            dir_path: Directory path
            filepath: Full file path
            filesize: File size in bytes
            created_date: File creation date
            modified_date: File modification date
            exif_data: EXIF metadata
            
        Returns:
            int: File ID in database
        """
        try:
            # Convert exif_data to JSON
            exif_json = json.dumps(exif_data)
            
            with db.get_cursor() as cur:
                # Check if file already exists
                cur.execute(
                    "SELECT id FROM files WHERE filepath = %s",
                    (filepath,)
                )
                result = cur.fetchone()
                
                if result:
                    # Update existing record
                    cur.execute(
                        """
                        UPDATE files 
                        SET filesize = %s, modified_date = %s, exif_data = %s, updated_at = NOW()
                        WHERE id = %s
                        RETURNING id
                        """,
                        (filesize, modified_date, exif_json, result['id'])
                    )
                    return cur.fetchone()['id']
                
                # Insert new file
                cur.execute(
                    """
                    INSERT INTO files
                    (filename, filepath, filesize, created_date, modified_date, exif_data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (filename, filepath, filesize, created_date, modified_date, exif_json)
                )
                return cur.fetchone()['id']
                
        except Exception as e:
            logger.error(f"Error storing file {filepath}: {e}")
            return None


# Create a scanner instance
scanner = FileScanner() 