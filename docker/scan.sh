#!/bin/bash
# Main scanning utility script for Docker-based execution
# This is the primary entry point for running the scanning utility

set -e  # Exit on error

cd "$(dirname "$0")/.." || exit 1

# Make sure config directory exists
mkdir -p config

# Default config file
CONFIG_FILE="config/scan_targets.yaml"

# Create example config if it doesn't exist
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating example configuration file..."
    cat > "$CONFIG_FILE" << EOF
# Scan target directories configuration
target_directories:
  # Personal photo directories - replace with actual paths
  personal:
    - path: /data/personal/photos1
      description: "Personal photos 2022"
      category: "P"  # P for Personal
    - path: /data/personal/photos2
      description: "Personal photos 2023"
      category: "P"
      
  # Work photo directories - replace with actual paths
  work:
    - path: /data/work/photos1
      description: "Client project photos"
      category: "W"  # W for Work
    - path: /data/work/photos2
      description: "Product photography"
      category: "W"

# Global scan settings
settings:
  recursive: true
  excluded_patterns:
    - "*StarQ*"
    - "export_*"
EOF
    echo "Created example configuration at $CONFIG_FILE"
    echo "⚠️  Please edit this file with your actual directories before running"
    echo "   Then run this script again to perform the scan"
    exit 0
fi

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
        --config|-c)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: docker/scan.sh [options]"
            echo
            echo "Options:"
            echo "  --verbose, -v         Enable verbose output"
            echo "  --group, -g GROUP     Only scan directories from this group"
            echo "  --config, -c FILE     Use specified config file (default: config/scan_targets.yaml)"
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

# Ensure Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "⚠️  Docker doesn't seem to be running. Please start Docker and try again."
    exit 1
fi

# Check if containers are built
if ! docker-compose ps -q app > /dev/null 2>&1; then
    echo "Building Docker containers..."
    docker-compose build
fi

# Ensure volume directories are accessible
echo "Ensuring volume directories are accessible..."
docker-compose run --rm --entrypoint "mkdir -p /data" app

# Run the scan
echo "Starting scan with configuration from $CONFIG_FILE..."
docker-compose run --rm app python -m src.scan_cli --config=$CONFIG_FILE $GROUP $VERBOSE

echo "✅ Scan complete!" 