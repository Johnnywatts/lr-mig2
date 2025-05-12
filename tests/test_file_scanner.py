"""
File: test_file_scanner.py
Purpose: Tests for the file scanner module
Version: 1.0.0
Last Updated: 2024-06-13
"""
import os
import shutil
import tempfile
from pathlib import Path
import pytest

from src.file_scanner import FileScanner

class TestFileScanner:
    """Test suite for the FileScanner class."""
    
    @pytest.fixture
    def setup_test_dir(self):
        """Create a temporary directory with test files."""
        # Create a temporary directory
        test_dir = tempfile.mkdtemp()
        
        try:
            # Create a subdirectory
            subdir = os.path.join(test_dir, "subdir")
            os.makedirs(subdir)
            
            # Create an excluded directory
            excluded_dir = os.path.join(test_dir, "3StarQ70")
            os.makedirs(excluded_dir)
            
            # Create test files
            with open(os.path.join(test_dir, "test.jpg"), "wb") as f:
                f.write(b"TEST JPEG")
                
            with open(os.path.join(subdir, "test.dng"), "wb") as f:
                f.write(b"TEST DNG")
                
            with open(os.path.join(excluded_dir, "excluded.jpg"), "wb") as f:
                f.write(b"EXCLUDED JPEG")
            
            yield test_dir
            
        finally:
            # Clean up
            shutil.rmtree(test_dir)
    
    def test_is_excluded_dir(self):
        """Test the is_excluded_dir method."""
        scanner = FileScanner()
        
        # Should be excluded
        assert scanner.is_excluded_dir("/path/to/3StarQ70")
        assert scanner.is_excluded_dir("/path/to/4StarQ90")
        
        # Should not be excluded
        assert not scanner.is_excluded_dir("/path/to/normal_dir")
        assert not scanner.is_excluded_dir("/path/to/photos")
    
    def test_scan_directory(self, setup_test_dir, monkeypatch):
        """Test the scan_directory method."""
        # Create a scanner with mocked database methods
        scanner = FileScanner()
        
        # Mock the _store_directory and _store_file methods
        scanner._store_directory = lambda dir_path, parent_path: 1
        scanner._store_file = lambda *args: 1
        
        # Mock the _extract_exif method to return empty dict
        scanner._extract_exif = lambda file_path: {}
        
        # Run the scan
        file_count = scanner.scan_directory(setup_test_dir)
        
        # We should have 2 files (test.jpg and subdir/test.dng)
        # The file in the excluded directory should be skipped
        assert file_count == 2 