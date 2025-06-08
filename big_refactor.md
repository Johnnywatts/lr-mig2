# Big Refactor: lr-mig2 Performance Optimization Plan

## Current System Status (Working Implementation)

### Overview
The lr-mig2 (Lightroom File Management Utility) is a Docker-based system for scanning, cataloging, and analyzing photography libraries across multiple drives. The current implementation successfully scans large photo collections but has significant performance bottlenecks.

### Core Architecture

#### 1. Database Layer (`src/database.py`)
- **PostgreSQL 14** running in Docker container
- Connection pooling with context managers
- Tables: `files`, `directories`, `duplicates`
- Current schema supports JSONB storage for EXIF data

#### 2. File Scanner (`src/file_scanner.py`)
- **Primary scanning engine** - 712 lines of code
- **Key Classes:**
  - `FileScanner`: Main scanning orchestrator
  - `PerformanceTracker`: Monitors scanning performance
  - `ProgressBar`: Console progress reporting
- **Current Performance**: ~9 files/second (single-threaded)
- **Supported Formats**: DNG, ARW, CR2, CR3, NEF, RAF, ORF, RW2, SRW, X3F, JPG, JPEG, TIF, TIFF, PNG, BMP

#### 3. Configuration Management
- **`src/config.py`**: Core configuration constants
- **`config/container_config.yaml`**: Docker mount points and database settings
- **`config/scan_targets_real.yaml`**: Directory scanning targets
- **Enhanced exclusion patterns** for Windows system directories

#### 4. Command Line Interface (`src/scan_cli.py`)
- **Entry point** for scanning operations
- Argument parsing for verbose output, group selection, config files
- Integration with logging system

#### 5. Logging System (`src/logger.py`)
- **Git-aware logging** with commit hash tracking
- **Dual output**: Console and file logging
- **Log files**: `logs/app_YYYY-MM-DD_commit-hash.log`
- **Structured performance tracking**

#### 6. Container Infrastructure
- **`docker/Dockerfile`**: Application container build
- **`real_scan.sh`**: Production scanning script with optimized PostgreSQL settings
- **`bootstrap.sh`**: Development/test scanning script
- **Network**: `lrmig2_network` for container communication

### Current Working Features

#### ✅ Successfully Implemented
1. **Large-scale scanning**: Processed 46,545+ files from 6.7TB RAID array
2. **Permission error handling**: Gracefully skips Windows system directories
3. **EXIF extraction**: Using fallback method (exifread + PIL)
4. **Database storage**: Files and metadata stored in PostgreSQL
5. **Progress tracking**: Real-time monitoring of scan progress
6. **Multi-drive support**: F: and G: drive scanning with proper mount points
7. **Error resilience**: Continues scanning despite individual file errors
8. **Docker integration**: Containerized with database persistence

#### 📊 Current Performance Metrics
- **Processing Rate**: ~9 files/second
- **Database Entries**: 46,545+ files processed
- **Total Discovery**: 197,560 files found across drives
- **EXIF Success**: Rich metadata extraction from Leica DNG files
- **Error Handling**: Graceful permission denied handling

### Key File References

#### Core Application Files 