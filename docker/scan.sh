#!/bin/bash
# Run scanning based on the scan configuration

set -e

cd "$(dirname "$0")/.." || exit 1

# Default config files
CONTAINER_CONFIG="config/container_config.yaml"
SCAN_CONFIG="config/scan_targets.yaml"

# Parse command line arguments
VERBOSE=""
GROUP=""

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
        --container-config|-c)
            CONTAINER_CONFIG="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: docker/scan.sh [options]"
            echo
            echo "Options:"
            echo "  --verbose, -v                 Enable verbose output"
            echo "  --group, -g GROUP             Only scan directories from this group"
            echo "  --scan-config, -s FILE        Use specified scan config file (default: config/scan_targets.yaml)"
            echo "  --container-config, -c FILE   Use specified container config file (default: config/container_config.yaml)"
            echo "  --help, -h                    Show this help message"
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

# Ensure config files exist
if [ ! -f "$CONTAINER_CONFIG" ]; then
    echo "Container configuration file not found: $CONTAINER_CONFIG"
    echo "Please create the container configuration file first."
    exit 1
fi

if [ ! -f "$SCAN_CONFIG" ]; then
    echo "Scan configuration file not found: $SCAN_CONFIG"
    echo "Please create the scan configuration file first."
    exit 1
fi

# Generate docker-compose file
echo "Generating Docker configuration..."
./docker/generate_compose.sh --config "$CONTAINER_CONFIG"

# Ensure Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "⚠️  Docker doesn't seem to be running. Please start Docker and try again."
    exit 1
fi

# Build containers if needed
if ! docker-compose ps -q app > /dev/null 2>&1; then
    echo "Building Docker containers..."
    docker-compose build
fi

# Run the scan
echo "Starting scan with configuration from $SCAN_CONFIG..."
docker-compose run --rm app python -m src.scan_cli --config="$SCAN_CONFIG" $GROUP $VERBOSE

echo "✅ Scan complete!" 