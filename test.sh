#!/bin/bash
# Run tests using Docker

# Set up error handling
set -e

# Get script directory (where this script is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

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
            echo "Usage: ./test.sh [options]"
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

# Create config directory if it doesn't exist
mkdir -p config

# Check if container config exists, create minimal test one if not
if [ ! -f "config/container_config.yaml" ]; then
    echo "Creating minimal container configuration..."
    cat > config/container_config.yaml << EOF
# Minimal container configuration for testing

# Database settings
database:
  host: db
  port: 5432
  name: lrmig2
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
    echo "Created minimal container configuration at config/container_config.yaml"
fi

# Create test scan config if it doesn't exist
if [ ! -f "config/scan_targets_testing.yaml" ]; then
    echo "Creating test scan configuration..."
    cat > config/scan_targets_testing.yaml << EOF
# Testing configuration for scanning
# This defines test directories within the project directory

target_directories:
  # Personal photo directories (test)
  personal:
    - path: /app/tests/test_data/personal
      description: "Personal test photos"
      category: "P"
      
  # Work photo directories (test)
  work:
    - path: /app/tests/test_data/work
      description: "Work test photos"
      category: "W"
      
  # Backup directories (test)
  backup:
    - path: /app/tests/test_data/backup
      description: "Backup test photos"
      category: null

# Global scan settings
settings:
  recursive: true
  excluded_patterns:
    - "*StarQ*"
    - "export_*"
EOF
    echo "Created test scan configuration at config/scan_targets_testing.yaml"
fi

# Create network if it doesn't exist
docker network inspect lrmig2_network >/dev/null 2>&1 || docker network create lrmig2_network

# Start PostgreSQL container if not running
if ! docker ps | grep -q lrmig2-db; then
    echo "Starting database container..."
    docker run -d --name lrmig2-db \
        --network lrmig2_network \
        -e POSTGRES_DB=lrmig2 \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=postgres \
        -v lrmig2_postgres_data:/var/lib/postgresql/data \
        -v "$(pwd)/sql/schema.sql:/docker-entrypoint-initdb.d/schema.sql" \
        postgres:14
    
    # Wait for PostgreSQL to be ready
    echo "Waiting for database to be ready..."
    for i in {1..30}; do
        if docker exec lrmig2-db pg_isready -U postgres &>/dev/null; then
            echo "Database is ready."
            break
        fi
        echo -n "."
        sleep 1
    done
    echo ""
fi

# Build the application image
echo "Building application image with latest dependencies..."
APP_IMAGE=$(docker build -q -f docker/Dockerfile .)

# Ensure the container has PyYAML installed
echo "Verifying required packages..."
if ! docker run --rm $APP_IMAGE pip list | grep -q PyYAML; then
    echo "Installing required packages..."
    docker run --rm \
        -v "$(pwd):/app" \
        $APP_IMAGE \
        pip install pyyaml
    # Rebuild the image with the new packages
    APP_IMAGE=$(docker build -q -f docker/Dockerfile .)
fi

# Generate test data
echo "Generating test data..."
docker run --rm \
    --name lrmig2-test-gen \
    --network lrmig2_network \
    -v "$(pwd):/app" \
    $APP_IMAGE \
    python tests/generate_test_data.py $CLEAN

# Run test scan
echo "Running test scan..."
docker run --rm \
    --name lrmig2-test-scan \
    --network lrmig2_network \
    -e DB_HOST=lrmig2-db \
    -e DB_PORT=5432 \
    -e DB_NAME=lrmig2 \
    -e DB_USER=postgres \
    -e DB_PASSWORD=postgres \
    -v "$(pwd):/app" \
    $APP_IMAGE \
    python -m src.scan_cli --config="config/scan_targets_testing.yaml" $GROUP $VERBOSE

echo "✅ Tests complete!" 