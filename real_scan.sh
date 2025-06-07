#!/bin/bash
# Run real library scan using Docker

# Set up error handling
set -e

# Get script directory (where this script is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Parse command line arguments
VERBOSE=""
GROUP=""
CONFIG="config/scan_targets_real.yaml"  # Default to real config

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
        --config)
            CONFIG="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: ./real_scan.sh [options]"
            echo
            echo "Options:"
            echo "  --verbose, -v         Enable verbose output"
            echo "  --group, -g GROUP     Only scan directories from this group"
            echo "  --config CONFIG       Use specified config file (default: config/scan_targets_real.yaml)"
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

# Check if container config exists, create minimal one if not
if [ ! -f "config/container_config.yaml" ]; then
    echo "Creating minimal container configuration..."
    cat > config/container_config.yaml << EOF
# Minimal container configuration for scanning

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
  # No external mount points needed for scanning
  mount_points: []
EOF
    echo "Created minimal container configuration at config/container_config.yaml"
fi

# Create network if it doesn't exist
docker network inspect lrmig2_network >/dev/null 2>&1 || docker network create lrmig2_network

# Start PostgreSQL container if not running
if ! docker ps -a | grep -q lrmig2-db; then
    # Container doesn't exist, create it
    echo "Starting database container..."
    docker run -d --name lrmig2-db \
        --network lrmig2_network \
        --cpus="6" \
        --memory="16g" \
        --memory-swap="16g" \
        -e POSTGRES_DB=lrmig2 \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_SHARED_BUFFERS=4GB \
        -e POSTGRES_EFFECTIVE_CACHE_SIZE=12GB \
        -e POSTGRES_WORK_MEM=256MB \
        -e POSTGRES_MAINTENANCE_WORK_MEM=1GB \
        -e POSTGRES_MAX_CONNECTIONS=50 \
        -e POSTGRES_CHECKPOINT_SEGMENTS=64 \
        -e POSTGRES_CHECKPOINT_COMPLETION_TARGET=0.9 \
        -e POSTGRES_WAL_BUFFERS=64MB \
        -v lrmig2_postgres_data:/var/lib/postgresql/data \
        -v "$(pwd)/sql/schema.sql:/docker-entrypoint-initdb.d/schema.sql" \
        postgres:14
elif ! docker ps | grep -q lrmig2-db; then
    # Container exists but is stopped, start it
    echo "Starting existing database container..."
    docker start lrmig2-db
else
    echo "Database container is already running."
fi

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

# Run real library scan
echo "Running real library scan with config: $CONFIG"
docker run --rm \
    --name lrmig2-real-scan \
    --network lrmig2_network \
    --cpus="16" \
    --memory="32g" \
    -e DB_HOST=lrmig2-db \
    -e DB_PORT=5432 \
    -e DB_NAME=lrmig2 \
    -e DB_USER=postgres \
    -e DB_PASSWORD=postgres \
    -e PYTHONUNBUFFERED=1 \
    -e OMP_NUM_THREADS=16 \
    -v "$(pwd):/app" \
    -v "/mnt/f:/mnt/f" \
    -v "/mnt/g:/mnt/g" \
    $APP_IMAGE \
    python -m src.scan_cli --config="$CONFIG" $GROUP $VERBOSE

echo "✅ Real library scan complete!" 