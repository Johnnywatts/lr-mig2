#!/bin/bash
# Run scanning based on YAML configuration in Docker

cd "$(dirname "$0")/.." || exit 1

# Ensure config directory exists
mkdir -p config

# Check if config file exists
if [ ! -f "config/scan_targets.yaml" ]; then
    echo "Creating example configuration file..."
    cat > config/scan_targets.yaml << EOF
# Example scan targets configuration
target_directories:
  # Example directories - replace with real paths
  test:
    - path: /app/tests
      description: "Test directory"
      category: "P"
      
# Global scan settings
settings:
  recursive: true
  excluded_patterns:
    - "*StarQ*"
EOF
    echo "Created example configuration at config/scan_targets.yaml"
    echo "Please edit this file with your actual directories before running"
    exit 0
fi

# Run the scan using the configuration
echo "Running scan with configuration from config/scan_targets.yaml..."
docker-compose run --rm app python -m src.scan_cli --config=config/scan_targets.yaml --verbose

echo "Scan complete!" 