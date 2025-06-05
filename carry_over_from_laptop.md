# Development Carry-Over Notes

## Current Status (June 5, 2025)

### Completed Work
- Implemented file scanning module with PyExifTool for better metadata extraction
- Added support for WSL2 path handling for Windows drives
- Successfully scanned test libraries from USB drive
- Fixed ExifTool termination issues during Python shutdown
- Updated database schema and connection handling

### Latest Changes
- Enhanced metadata extraction with PyExifTool integration
- Added fallback methods when ExifTool is not available
- Created scan_targets_usb.yaml for testing with real data
- Fixed error handling during application shutdown

### Environment Setup
1. Database:
   - PostgreSQL database running in Docker
   - Connection details in .env file (localhost:5432, user: postgres, password: postgres)

2. Dependencies:
   - Updated requirements.txt with new dependencies (pyexiftool)
   - System dependency: exiftool package must be installed

3. Testing Configuration:
   - Test USB drive was mounted at /mnt/f
   - Contains main_lib (with files removed) and backup_lib (complete set)
   - Successful scan processed 274 files

## Next Steps

### Immediate Tasks
1. Run scanner against real Lightroom libraries to gather comprehensive metadata
2. Query database to determine common patterns and edge cases
3. Implement file comparison logic between libraries:
   - Exact matches (same name, size, metadata)
   - Partial matches (missing files from one directory)
   - Misplaced files (same file in wrong category)

### File Comparison Requirements
- Compare files based on name, size, and key EXIF attributes
- Identify which files exist in backup_lib but not in main_lib
- Generate reports showing file distribution across libraries
- Handle different file versions (edited vs original)

### Setup on New Machine
1. Install dependencies:
   ```bash
   sudo apt-get install exiftool
   pip install -r requirements.txt
   ```

2. Start database:
   ```bash
   docker-compose up -d db
   ```

3. Configure environment:
   - Create .env file with database credentials
   - Ensure drive mount points are correctly configured for the new machine

4. Run tests:
   ```bash
   pytest -xvs tests/test_file_scanner.py
   ```

## Database Queries for Analysis

Once real libraries are scanned, use these queries to analyze the data:

```sql
-- Count files by directory
SELECT dirpath, COUNT(*) as file_count 
FROM files 
JOIN directories ON files.dirpath = directories.dirpath 
GROUP BY dirpath 
ORDER BY file_count DESC;

-- Find potential duplicates (same name, different paths)
SELECT filename, COUNT(*) as occurrences 
FROM files 
GROUP BY filename 
HAVING COUNT(*) > 1;

-- Compare file sizes for potential duplicates
SELECT f1.filename, f1.filepath as path1, f2.filepath as path2, 
       f1.filesize as size1, f2.filesize as size2
FROM files f1
JOIN files f2 ON f1.filename = f2.filename AND f1.filepath != f2.filepath;
```
```

3. Now, let's commit all changes:

```bash
cd /home/alexj/repos/lr-mig2

# Add all files
git add src/file_scanner.py
git add config/scan_targets_usb.yaml
git add progress.md
git add carry_over_from_laptop.md
git add .env

# Commit with a meaningful message
git commit -m "Enhance file scanning with PyExifTool and add USB drive support"

# Push changes to remote repository (if desired)
git push
```

These steps will document your progress, provide clear instructions for continuing on a different machine, and save all your changes to version control.
