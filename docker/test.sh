#!/bin/bash
# Run tests with the test data and testing configuration

set -e  # Exit on error

cd "$(dirname "$0")/.." || exit 1

# Default config files
CONTAINER_CONFIG="config/container_config.yaml"
SCAN_CONFIG="config/scan_targets_testing.yaml"

# Parse command line arguments
VERBOSE=""
GROUP=""
CLEAN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE="--verbose"
            shift
            ;;
        --group|-g)
            GROUP="--group $2"
            shift 2
            ;;
        --clean|-c)
            CLEAN="--clean"
            shift
            ;;
        --help|-h)
            echo "Usage: docker/test.sh [options]"
            echo
            echo "Options:"
            echo "  --verbose, -v         Enable verbose output"
            echo "  --group, -g GROUP     Only scan directories from this group"
            echo "  --clean, -c           Clean existing test data before generating"
            echo "  --help, -h            Show this help message"
            echo
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Ensure configuration files exist
mkdir -p config

# Create testing scan config if it doesn't exist
if [ ! -f "$SCAN_CONFIG" ]; then
    echo "Creating test scan configuration file..."
    cat > "$SCAN_CONFIG" << EOF
# Testing configuration for scanning
# This defines test directories within the project directory

target_directories:
  # Personal photo directories (test)
  personal:
    - path: /app/tests/test_data/personal
      description: "Personal test photos"
      category: "P"  # P for Personal
      
  # Work photo directories (test)
  work:
    - path: /app/tests/test_data/work
      description: "Work test photos"
      category: "W"  # W for Work
      
  # Backup directories (test)
  backup:
    - path: /app/tests/test_data/backup
      description: "Backup test photos"
      category: null  # Will be assigned during processing

# Global scan settings
settings:
  recursive: true
  excluded_patterns:
    - "*StarQ*"
    - "export_*"
EOF
    echo "Created test scan configuration at $SCAN_CONFIG"
fi

# Ensure container config exists or create minimal one
if [ ! -f "$CONTAINER_CONFIG" ]; then
    echo "Creating minimal container configuration file..."
    cat > "$CONTAINER_CONFIG" << EOF
# Minimal container configuration for testing

# Database settings
database:
  host: db
  port: 5432
  name: lrmig2_test
  user: postgres
  password: postgres

# Application settings
application:
  log_level: INFO
  
# Container settings
container:
  # No external mount points needed for testing
  mount_points: []
EOF
    echo "Created minimal container configuration at $CONTAINER_CONFIG"
fi

# Ensure Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "⚠️  Docker doesn't seem to be running. Please start Docker and try again."
    exit 1
fi

# Generate docker-compose file
echo "Generating Docker configuration..."
./docker/generate_compose.sh --config "$CONTAINER_CONFIG"

# Build containers if needed
if ! docker-compose ps -q app > /dev/null 2>&1; then
    echo "Building Docker containers..."
    docker-compose build
fi

# Generate test data
echo "Generating test data..."
docker-compose run --rm app python tests/generate_test_data.py $CLEAN

# Run a test scan
echo "Running test scan..."
docker-compose run --rm app python -m src.scan_cli --config="$SCAN_CONFIG" $GROUP $VERBOSE

echo "✅ Tests complete!" 