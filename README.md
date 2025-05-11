# lr-mig2
Lightroom File Management Utility

## Overview
A Docker-based utility for rationalizing multiple Lightroom libraries and backup directories. This tool helps identify and manage duplicate photography files, misallocated directories, and unused storage space across multiple Lightroom installations.

## Problem Statement
- Multiple Lightroom libraries (Personal and Work photography)
- Multiple backup directories created over several years
- Files and directories potentially duplicated across locations
- Some folders incorrectly categorized (e.g., personal photos in work library)

## Technical Requirements

### File Formats Supported
- DNG (Leica cameras)
- Proprietary RAW formats (Sony, Canon)
- JPEG (excluding export directories)

### Special Cases
- Export directories (named '3StarQ70' or '_N_StarQxx') are excluded from comparison
- These are Lightroom-generated JPEGs stored in subdirectories
- Quality indicators (N) represent subjective curation ratings

## System Architecture

### Technology Stack
- **Container**: Docker
- **Database**: PostgreSQL
- **Primary Language**: Python
- **Development Environment**: Cursor IDE with Claude Sonnet 3.7

### Database Requirements
- PostgreSQL 14+
- Tables for:
  - File metadata
  - Directory structures
  - Category assignments
  - Duplicate tracking

## Processing Workflow

1. **Initial Scan**
   - Scan target directories
   - Build database of files and metadata
   - Record directory locations and full paths

2. **Category Assignment**
   - User reviews directory list
   - Assigns categories via spreadsheet (category_assignment.csv)
   - Categories: P (Personal) or W (Work)

3. **Library Integration**
   - User provides primary library locations
   - System assigns categories to all subfolders
   - User reviews and corrects miscategorizations

4. **Duplicate Detection**
   - **Exact Duplicates**: Same name, file count, and size
   - **Partial Duplicates**: 
     - "Folder duplicate plus y%": Backup has additional files
     - "Folder duplicate minus y%": Backup has fewer files
   - Excludes export directories (NStarQxx)

## Development Guidelines

### Code Standards
- Python 3.9+ required
- Follow PEP 8 style guide
- Include type hints
- Document all functions and classes

### Testing Requirements
- Unit tests for all core functions
- Integration tests for database operations
- Test data sets for edge cases
- Automated test suite

### Version Control
- One functional area per commit
- Meaningful commit messages
- Regular commits
- Feature branches for new development

### Documentation
- Maintain DEVELOPMENT_PLAN.md
- Update version numbers on completed tasks
- Document all API endpoints
- Include setup instructions

### Logging Standards
- All logs are kept in version control in the `logs` directory
- Log files are named with date and git commit information: `tests_YYYY-MM-DD_commit:hash_date:date.log`
- This allows easy correlation between:
  - Test results
  - Code state (via commit hash)
  - Timeline of changes
- Log format includes:
  - Timestamp
  - Logger name
  - Log level
  - Message
  - Git commit information
- Log levels should be used appropriately:
  - DEBUG: Detailed information for debugging
  - INFO: General operational information
  - WARNING: Warning messages for potentially harmful situations
  - ERROR: Error events that might still allow the application to continue
  - CRITICAL: Critical events that may lead to application termination

### Benefits of Keeping Logs
- Historical debugging capability
- Performance tracking over time
- Easy rollback reference
- Correlation between code changes and test results
- Documentation of system behavior across different states

## Roadmap

### Phase 1: Foundation (Current)
- [ ] File scanning implementation
- [ ] Metadata extraction and storage
- [ ] Basic database schema
- [ ] Initial test suite

### Phase 2: Categorization
- [ ] Manual category assignment interface
- [ ] Category validation tools
- [ ] User review workflow
- [ ] Category correction tools

### Phase 3: Analysis
- [ ] Duplicate detection algorithms
- [ ] Directory comparison tools
- [ ] Misallocation detection
- [ ] Storage optimization analysis

### Phase 4: Management
- [ ] File movement functions
- [ ] Directory reorganization
- [ ] Audit logging
- [ ] Recovery procedures

### Phase 5: Cleanup
- [ ] Safe deletion procedures
- [ ] Backup to slow storage
- [ ] Recovery verification
- [ ] Final cleanup tools

## Getting Started

### Prerequisites
- Docker 20.10+
- PostgreSQL 14+
- Python 3.9+
- Lightroom Classic (for reference)

### Installation
1. Clone the repository
2. Build the Docker container
3. Configure database connection
4. Run initial setup script

### Usage
1. Configure target directories
2. Run initial scan
3. Review and assign categories
4. Execute analysis
5. Review and confirm changes
6. Execute cleanup

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License
[License information to be added]

## Contact
[Contact information to be added]


