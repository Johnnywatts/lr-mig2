#!/bin/bash
# Bootstrap script to run the application with Docker

# Set up error handling
set -e

# Get script directory (where this script is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create config directory if it doesn't exist
mkdir -p config

# Check if container config exists, create default if not
if [ ! -f "config/container_config.yaml" ]; then
    echo "Creating default container configuration..."
    cat > config/container_config.yaml << EOF
# Container configuration for the Lightroom File Management Utility

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
  # Base directories to mount - customize these for your environment
  mount_points:
    - host_path: /path/to/photos      # Path on host machine
      container_path: /data/photos    # Path in container
EOF
    echo "Created default container config file at config/container_config.yaml"
    echo "Please edit this file to specify your photo directories."
    exit 1
fi

# Check if scan config exists, create default if not
if [ ! -f "config/scan_targets.yaml" ]; then
    echo "Creating default scan configuration..."
    cat > config/scan_targets.yaml << EOF
# Target directories for scanning

target_directories:
  # Personal photo directories
  personal:
    - path: /data/photos/personal
      description: "Personal photos"
      category: "P"  # P for Personal
      
# Global scan settings
settings:
  recursive: true
  excluded_patterns:
    - "*StarQ*"
    - "export_*"
EOF
    echo "Created default scan config file at config/scan_targets.yaml"
    echo "Please edit this file to specify which directories to scan."
    exit 1
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

# Parse command line arguments
VERBOSE=""
GROUP=""
SCAN_CONFIG="config/scan_targets.yaml"

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
        --scan-config|-s)
            SCAN_CONFIG="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: ./bootstrap.sh [options]"
            echo
            echo "Options:"
            echo "  --verbose, -v               Enable verbose output"
            echo "  --group, -g GROUP           Only scan directories from this group"
            echo "  --scan-config, -s FILE      Use specified scan config file (default: config/scan_targets.yaml)"
            echo "  --help, -h                  Show this help message"
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

# Run the application container
echo "Starting application container..."
docker run --rm \
    --name lrmig2-app \
    --network lrmig2_network \
    -e DB_HOST=lrmig2-db \
    -e DB_PORT=5432 \
    -e DB_NAME=lrmig2 \
    -e DB_USER=postgres \
    -e DB_PASSWORD=postgres \
    -v "$(pwd):/app" \
    $APP_IMAGE \
    python -m src.scan_cli --config="$SCAN_CONFIG" $GROUP $VERBOSE

echo "✅ Scan complete!" 