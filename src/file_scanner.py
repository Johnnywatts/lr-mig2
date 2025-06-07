"""
File: file_scanner.py
Purpose: Scans directories for image files and extracts metadata
Version: 1.1.0 - Performance Enhanced
Last Updated: 2025-06-05
"""
import os
import logging
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
import fnmatch
import subprocess
from src.config import SUPPORTED_RAW_FORMATS, EXCLUDED_DIRS
from src.database import db
import uuid
import sys

# Set up logging
logger = logging.getLogger(__name__)

# Define module-level variables
EXIFTOOL_AVAILABLE = False

# Import dependencies
try:
    import exiftool
    EXIFTOOL_AVAILABLE = True
except ImportError:
    logger.warning("PyExifTool not installed. Falling back to basic metadata extraction.")
    # Keep the old imports as fallback
    import exifread
    from PIL import Image

class PerformanceTracker:
    """Tracks performance metrics during scanning."""
    
    def __init__(self, report_interval: int = 50):
        self.start_time = time.time()
        self.last_report_time = self.start_time
        self.report_interval = report_interval
        
        # Counters
        self.files_processed = 0
        self.total_file_size = 0
        self.directories_processed = 0
        self.files_successful = 0
        self.files_failed = 0
        
        # Timing accumulators
        self.total_file_processing_time = 0.0
        self.total_exif_extraction_time = 0.0
        self.total_db_storage_time = 0.0
        
        # Performance history for moving average
        self.recent_processing_times = []
        self.max_recent_samples = 50
        
    def start_file_processing(self):
        """Start timing file processing."""
        return time.time()
    
    def end_file_processing(self, start_time: float, file_size: int = 0, success: bool = True):
        """End timing file processing and update stats."""
        processing_time = time.time() - start_time
        self.total_file_processing_time += processing_time
        self.files_processed += 1
        self.total_file_size += file_size
        
        # Track recent processing times for moving average
        self.recent_processing_times.append(processing_time)
        if len(self.recent_processing_times) > self.max_recent_samples:
            self.recent_processing_times.pop(0)
        
        # Report progress periodically
        if self.files_processed % self.report_interval == 0:
            self._report_progress()
        
        if success:
            self.files_successful += 1
        else:
            self.files_failed += 1
    
    def time_operation(self, operation_name: str):
        """Context manager for timing operations."""
        return TimingContext(self, operation_name)
    
    def _report_progress(self):
        """Report current progress and performance."""
        current_time = time.time()
        elapsed_total = current_time - self.start_time
        elapsed_since_last = current_time - self.last_report_time
        
        # Calculate rates
        overall_rate = self.files_processed / elapsed_total if elapsed_total > 0 else 0
        recent_rate = self.report_interval / elapsed_since_last if elapsed_since_last > 0 else 0
        
        # Calculate average processing time
        avg_processing_time = (self.total_file_processing_time / self.files_processed 
                             if self.files_processed > 0 else 0)
        
        # Calculate recent average (moving average)
        recent_avg_time = (sum(self.recent_processing_times) / len(self.recent_processing_times)
                          if self.recent_processing_times else 0)
        
        # Calculate data throughput
        data_rate_mb = (self.total_file_size / (1024 * 1024)) / elapsed_total if elapsed_total > 0 else 0
        
        logger.info(f"🚀 Progress: {self.files_processed} files processed")
        logger.info(f"⚡ Performance: {overall_rate:.1f} files/sec overall, {recent_rate:.1f} files/sec recent")
        logger.info(f"⏱️  Timing: {avg_processing_time:.3f}s avg/file, {recent_avg_time:.3f}s recent avg")
        logger.info(f"💾 Data: {data_rate_mb:.1f} MB/sec")
        logger.info(f"🕐 Elapsed: {timedelta(seconds=int(elapsed_total))}")
        
        self.last_report_time = current_time
    
    def add_exif_time(self, duration: float):
        """Add EXIF extraction time."""
        self.total_exif_extraction_time += duration
    
    def add_db_time(self, duration: float):
        """Add database storage time."""
        self.total_db_storage_time += duration
    
    def add_directory(self):
        """Increment directory counter."""
        self.directories_processed += 1
    
    def get_final_report(self) -> Dict[str, Any]:
        """Get final performance report."""
        total_time = time.time() - self.start_time
        
        return {
            'total_time': total_time,
            'files_processed': self.files_processed,
            'files_successful': self.files_successful,
            'files_failed': self.files_failed,
            'directories_processed': self.directories_processed,
            'total_file_size_mb': self.total_file_size / (1024 * 1024),
            'overall_rate_files_per_sec': self.files_processed / total_time if total_time > 0 else 0,
            'data_rate_mb_per_sec': (self.total_file_size / (1024 * 1024)) / total_time if total_time > 0 else 0,
            'avg_file_processing_time': self.total_file_processing_time / self.files_processed if self.files_processed > 0 else 0,
            'avg_exif_extraction_time': self.total_exif_extraction_time / self.files_processed if self.files_processed > 0 else 0,
            'avg_db_storage_time': self.total_db_storage_time / self.files_processed if self.files_processed > 0 else 0,
            'exif_time_percentage': (self.total_exif_extraction_time / self.total_file_processing_time * 100) if self.total_file_processing_time > 0 else 0,
            'db_time_percentage': (self.total_db_storage_time / self.total_file_processing_time * 100) if self.total_file_processing_time > 0 else 0
        }

class TimingContext:
    """Context manager for timing operations."""
    
    def __init__(self, tracker, operation: str):
        self.tracker = tracker
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if self.operation == 'exif':
            self.tracker.add_exif_time(duration)
        elif self.operation == 'db':
            self.tracker.add_db_time(duration)

class ProgressBar:
    """Simple progress bar that updates in place."""
    
    def __init__(self, total: int, width: int = 50):
        self.total = total
        self.width = width
        self.current = 0
    
    def update(self, current: int, extra_info: str = ""):
        """Update progress bar."""
        self.current = current
        if self.total == 0:
            percent = 0
        else:
            percent = min(100, (current / self.total) * 100)
        
        filled = int(self.width * current // self.total) if self.total > 0 else 0
        bar = '█' * filled + '░' * (self.width - filled)
        
        # Clear line and print progress - fix for Docker
        print(f'\r🚀 Progress: {bar} {percent:.1f}% ({current:,}/{self.total:,}) {extra_info}', end='', flush=True)
    
    def finish(self, final_message: str = ""):
        """Complete the progress bar."""
        sys.stdout.write(f'\n✅ {final_message}\n')
        sys.stdout.flush()

class FileScanner:
    """Scans directories for image files and extracts metadata."""
    
    def __init__(self, performance_reporting: bool = True, report_interval: int = 50, 
                 use_db_logging: bool = True):
        """Initialize the file scanner.
        
        Args:
            performance_reporting: Enable detailed performance tracking
            report_interval: Number of files between progress reports
            use_db_logging: Enable database logging
        """
        self.supported_extensions = set(SUPPORTED_RAW_FORMATS + ['.jpg', '.jpeg'])
        self.excluded_patterns = EXCLUDED_DIRS
        self.et = None
        self.performance_reporting = performance_reporting
        self.performance_tracker = PerformanceTracker(report_interval) if performance_reporting else None
        
        # Initialize ExifTool if available
        if EXIFTOOL_AVAILABLE:
            try:
                self.et = exiftool.ExifToolHelper()
                logger.info("ExifTool initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize ExifTool: {e}")
        
        # Generate unique session ID for this scan
        self.scan_session_id = str(uuid.uuid4())
        logger.info(f"🔍 Scan session ID: {self.scan_session_id}")
        
        # Initialize database logger
        if use_db_logging:
            from src.db_logger import DatabaseLogger
            self.db_logger = DatabaseLogger(self.scan_session_id, "file_scanner")
        else:
            self.db_logger = None
        
        # Suppress verbose exifread debug logging
        logging.getLogger('exifread').setLevel(logging.WARNING)
        
        # Also suppress PIL debug if it's noisy
        logging.getLogger('PIL').setLevel(logging.WARNING)
        
        # Track if we've already warned about fallback method
        self._fallback_warning_shown = False
        
        self.progress_bar = None
    
    def cleanup(self):
        """Explicitly clean up resources before shutdown."""
        if self.et is not None:
            try:
                self.et.terminate()
            except Exception as e:
                logger.warning(f"Error terminating ExifTool: {e}")
            finally:
                # Set to None to prevent library's __del__ from being called
                self.et = None
    
    def __del__(self):
        """Simplified destructor to avoid shutdown errors."""
        pass
    
    def is_excluded_dir(self, dirpath: str) -> bool:
        """Check if directory should be excluded based on patterns.
        
        Args:
            dirpath: Directory path to check
            
        Returns:
            bool: True if directory should be excluded, False otherwise
        """
        dir_name = os.path.basename(dirpath)
        return any(fnmatch.fnmatch(dir_name, pattern) for pattern in self.excluded_patterns)
    
    def _is_supported_file(self, filename: str) -> bool:
        """Check if file is a supported image format."""
        if not filename:
            return False
            
        file_ext = Path(filename).suffix.lower()
        
        # Remove the leading dot
        if file_ext.startswith('.'):
            file_ext = file_ext[1:]
        
        # Check against supported formats from config
        return file_ext in SUPPORTED_RAW_FORMATS
    
    def _should_exclude_directory(self, dirname: str) -> bool:
        """Check if directory should be excluded based on patterns."""
        if not dirname:
            return False
            
        # Check against excluded directory patterns
        for pattern in EXCLUDED_DIRS:
            if fnmatch.fnmatch(dirname.lower(), pattern.lower()):
                return True
        
        # Also exclude hidden directories (starting with .)
        if dirname.startswith('.'):
            return True
            
        return False
    
    def _count_total_files(self, directory: str, recursive: bool = True) -> int:
        """Count total files before processing for progress tracking."""
        logger.info(f"🔍 Counting files in {directory}...")
        total_files = 0
        
        try:
            if recursive:
                for root, dirs, files in os.walk(directory):
                    # Apply exclusion filters
                    dirs[:] = [d for d in dirs if not self._should_exclude_directory(d)]
                    
                    for file in files:
                        if self._is_supported_file(file):
                            total_files += 1
                            
                            # Show counting progress every 1000 files
                            if total_files % 1000 == 0:
                                sys.stdout.write(f'\r🔍 Found {total_files:,} files...')
                                sys.stdout.flush()
            else:
                files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
                total_files = len([f for f in files if self._is_supported_file(f)])
        
        except Exception as e:
            logger.warning(f"Error counting files in {directory}: {e}")
            return 0
        
        sys.stdout.write(f'\r✅ Found {total_files:,} files total\n')
        return total_files
    
    def scan_directory(self, directory: str, recursive: bool = True) -> int:
        """Scan directory with progress bar."""
        logger.info(f"🚀 Starting PERFORMANCE-ENHANCED scan of directory: {directory}")
        
        # Count total files first
        total_files = self._count_total_files(directory, recursive)
        
        if total_files == 0:
            logger.warning("No supported files found.")
            return 0
        
        # TODO: Progress bar doesn't refresh properly in Docker container
        # Need to fix console output buffering/carriage return handling
        # self.progress_bar = ProgressBar(total_files)
        
        start_time = time.time()
        files_processed = 0
        
        # Store top-level directory
        self._store_directory(directory, None)
        
        # Keep track of directories already in DB
        processed_dirs = set()
        processed_dirs.add(directory)
        
        # Walk through directory
        for dirpath, dirnames, filenames in os.walk(directory):
            # Skip excluded directories
            if self.is_excluded_dir(dirpath):
                logger.debug(f"Skipping excluded directory: {dirpath}")
                dirnames.clear()  # This prevents os.walk from recursing into this dir
                continue
            
            # Store directory info if it's a subdirectory
            dir_path_obj = Path(dirpath)
            if dirpath != directory:
                parent_path = str(dir_path_obj.parent)
                if parent_path in processed_dirs:
                    self._store_directory(dirpath, parent_path)
                    processed_dirs.add(dirpath)
            
            # Process files
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if self._process_file(file_path):
                    files_processed += 1
            
            # Stop recursion if not requested
            if not recursive:
                break
            
            if files_processed % 10 == 0:  # Update every 10 files instead of 50
                elapsed = time.time() - start_time
                files_per_sec = files_processed / elapsed if elapsed > 0 else 0
                
                extra_info = f"({files_per_sec:.1f} files/sec)"
                # self.progress_bar.update(files_processed, extra_info)
            
            # Simple progress logging every 1000 files
            if files_processed % 1000 == 0:
                elapsed = time.time() - start_time
                files_per_sec = files_processed / elapsed if elapsed > 0 else 0
                percent = (files_processed / total_files) * 100 if total_files > 0 else 0
                
                logger.info(f"📊 Progress: {files_processed:,}/{total_files:,} ({percent:.1f}%) - {files_per_sec:.1f} files/sec")
        
        # Generate final performance report
        if self.performance_tracker:
            final_report = self.performance_tracker.get_final_report()
            
            # Get error/warning counts from database logger
            error_count = self.db_logger.get_error_count() if self.db_logger else 0
            warning_count = self.db_logger.get_warning_count() if self.db_logger else 0
            
            logger.info("=" * 70)
            logger.info("🏁 FINAL PERFORMANCE REPORT")
            logger.info("=" * 70)
            logger.info(f"⏱️  Total time: {timedelta(seconds=int(final_report['total_time']))}")
            logger.info(f"📁 Files processed: {final_report['files_processed']:,}")
            logger.info(f"✅ Files successful: {final_report['files_successful']:,}")
            logger.info(f"❌ Files failed: {final_report['files_failed']:,}")
            logger.info(f"⚠️  Warnings: {warning_count:,}")
            logger.info(f"🚨 Errors: {error_count:,}")
            logger.info(f"📊 Success rate: {(final_report['files_successful']/final_report['files_processed']*100):.1f}%")
            logger.info(f"📂 Directories processed: {final_report['directories_processed']:,}")
            logger.info(f"💾 Data processed: {final_report['total_file_size_mb']:.1f} MB")
            logger.info(f"⚡ Overall rate: {final_report['overall_rate_files_per_sec']:.2f} files/sec")
            logger.info(f"🌊 Data rate: {final_report['data_rate_mb_per_sec']:.2f} MB/sec")
            logger.info(f"📊 Average time per file: {final_report['avg_file_processing_time']:.3f}s")
            logger.info(f"🔍 Average EXIF time: {final_report['avg_exif_extraction_time']:.3f}s ({final_report['exif_time_percentage']:.1f}%)")
            logger.info(f"💿 Average DB time: {final_report['avg_db_storage_time']:.3f}s ({final_report['db_time_percentage']:.1f}%)")
            
            # Add error breakdown if there were issues
            if error_count > 0 or warning_count > 0:
                logger.info("─" * 70)
                logger.info("📋 ISSUE SUMMARY:")
                if warning_count > 0:
                    logger.info(f"⚠️  {warning_count} warnings (e.g., Unicode data sanitized)")
                if error_count > 0:
                    logger.info(f"🚨 {error_count} errors (files that couldn't be processed)")
                logger.info("💡 Run database queries to analyze specific issues")
            
            logger.info("=" * 70)
        
        # TODO: Uncomment when progress bar display is fixed
        # if self.progress_bar:
        #     self.progress_bar.finish(f"Completed! {files_processed:,} files processed")
        
        logger.info(f"✅ Completed scanning {directory}. Processed {files_processed:,} files")
        return files_processed
    
    def _process_file(self, file_path: str) -> bool:
        """Process a single file, extracting metadata and storing in DB.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if file was processed, False otherwise
        """
        path_obj = Path(file_path)
        
        # Skip if not a supported file type
        if not self._is_supported_file(path_obj.name):
            return False
        
        # Start performance tracking
        processing_start = self.performance_tracker.start_file_processing() if self.performance_tracker else None
        
        try:
            # Get file stats
            file_stats = path_obj.stat()
            file_size = file_stats.st_size
            created_date = datetime.fromtimestamp(file_stats.st_ctime)
            modified_date = datetime.fromtimestamp(file_stats.st_mtime)
            
            # Extract EXIF data with timing
            exif_data = self._extract_exif(file_path)
            
            # Store in database with timing
            self._store_file(
                path_obj.name,
                str(path_obj.parent),
                file_path,
                file_size,
                created_date,
                modified_date,
                exif_data
            )
            
            # End performance tracking
            if self.performance_tracker:
                self.performance_tracker.end_file_processing(processing_start, file_size, success=True)
            
            return True
            
        except Exception as e:
            if self.db_logger:
                self.db_logger.log("ERROR", f"Failed to process file: {str(e)}", file_path, 
                                  {"error_type": type(e).__name__, "error_details": str(e)})
            # Don't log to console - only to database
            if self.performance_tracker:
                self.performance_tracker.end_file_processing(processing_start, 0, success=False)
            return False
    
    def _extract_exif(self, file_path: str) -> Dict[str, Any]:
        """Extract EXIF data from image file using ExifTool."""
        exif_data = {}
        
        # Time the EXIF extraction
        timing_context = self.performance_tracker.time_operation('exif') if self.performance_tracker else None
        
        try:
            if timing_context:
                timing_context.__enter__()
            
            # Use ExifTool if available (preferred method)
            if self.et is not None:
                metadata = self.et.get_metadata(file_path)
                
                # Convert metadata to a flat dictionary with string values
                if isinstance(metadata, dict):
                    # Handle dictionary return
                    for key, value in metadata.items():
                        # Skip binary data
                        if isinstance(value, bytes):
                            continue
                        # Convert values to strings to ensure they're serializable
                        if hasattr(value, '__str__'):
                            exif_data[key] = str(value)
                elif isinstance(metadata, list) and len(metadata) > 0:
                    # Handle list return - take the first item if it's a dictionary
                    if isinstance(metadata[0], dict):
                        for key, value in metadata[0].items():
                            if isinstance(value, bytes):
                                continue
                            if hasattr(value, '__str__'):
                                exif_data[key] = str(value)
                    else:
                        # Just store the raw values as numbered keys
                        for i, value in enumerate(metadata):
                            if isinstance(value, bytes):
                                continue
                            if hasattr(value, '__str__'):
                                exif_data[f"value_{i}"] = str(value)
                
                return exif_data
                
            # Fallback to old method if ExifTool is not available
            # Only log this warning once, not for every file
            if not self._fallback_warning_shown:
                logger.info("📋 Using fallback EXIF extraction (PyExifTool not available)")
                self._fallback_warning_shown = True
            
            # For RAW files use exifread
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
        
        finally:
            if timing_context:
                timing_context.__exit__(None, None, None)
        
        return exif_data
    
    def _sanitize_exif_for_json(self, exif_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize EXIF data for safe JSON storage."""
        sanitized = {}
        for key, value in exif_data.items():
            try:
                if isinstance(value, str):
                    # Remove null bytes and other problematic Unicode
                    clean_value = value.replace('\u0000', '').replace('\x00', '')
                    # Remove other control characters
                    clean_value = ''.join(char for char in clean_value if ord(char) >= 32 or char in '\t\n\r')
                    sanitized[key] = clean_value
                else:
                    sanitized[key] = str(value)
            except (UnicodeError, TypeError):
                sanitized[key] = f"<unsupported_data_type_{type(value).__name__}>"
        return sanitized
    
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
                    if self.performance_tracker:
                        self.performance_tracker.add_directory()
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
                
                if self.performance_tracker:
                    self.performance_tracker.add_directory()
                
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
        """Store file metadata in the database with robust Unicode handling."""
        timing_context = self.performance_tracker.time_operation('db') if self.performance_tracker else None
        
        try:
            if timing_context:
                timing_context.__enter__()
            
            # Robust EXIF JSON conversion with Unicode error handling
            try:
                sanitized_exif = self._sanitize_exif_for_json(exif_data)
                exif_json = json.dumps(sanitized_exif, ensure_ascii=False)
            except (UnicodeDecodeError, UnicodeEncodeError) as e:
                logger.warning(f"Unicode error in EXIF for {filepath}, sanitizing data: {e}")
                # Sanitize EXIF data by removing problematic characters
                sanitized_exif = {}
                for key, value in exif_data.items():
                    try:
                        # Try to encode/decode to catch problematic characters
                        if isinstance(value, str):
                            sanitized_value = value.encode('utf-8', errors='replace').decode('utf-8')
                        else:
                            sanitized_value = str(value).encode('utf-8', errors='replace').decode('utf-8')
                        sanitized_exif[key] = sanitized_value
                    except Exception:
                        # If all else fails, convert to safe string
                        sanitized_exif[key] = f"<encoding_error>_{type(value).__name__}"
                
                exif_json = json.dumps(sanitized_exif, ensure_ascii=False)
            
            with db.get_cursor() as cur:
                # ALWAYS INSERT - no checking for existing files
                cur.execute(
                    """
                    INSERT INTO files
                    (filename, filepath, filesize, created_date, modified_date, exif_data, scan_session_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (filename, filepath, filesize, created_date, modified_date, exif_json, self.scan_session_id)
                )
                return cur.fetchone()['id']
                
        except Exception as e:
            if self.db_logger:
                self.db_logger.log("ERROR", f"Failed to store file: {str(e)}", filepath, 
                                  {"error_type": type(e).__name__, "error_details": str(e)})
            # Don't log to console - only to database
            return False
        
        finally:
            if timing_context:
                timing_context.__exit__(None, None, None)


# Create a scanner instance with performance tracking enabled
scanner = FileScanner(performance_reporting=True, report_interval=50) 