#!/bin/bash
# Generate docker-compose.yml from container configuration

set -e

# Default config file
CONFIG_FILE="config/container_config.yaml"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --config|-c)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: docker/generate_compose.sh [options]"
            echo
            echo "Options:"
            echo "  --config, -c FILE     Use specified container config file (default: config/container_config.yaml)"
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

# Make sure config directory exists
mkdir -p config

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Container configuration file not found: $CONFIG_FILE"
    echo "Please create the container configuration file first."
    exit 1
fi

# Extract mount points using Python
MOUNTS=$(python3 - <<EOF
import yaml
import sys

try:
    with open("$CONFIG_FILE", 'r') as f:
        config = yaml.safe_load(f)
    
    container_config = config.get('container', {})
    mount_points = container_config.get('mount_points', [])
    
    for mount in mount_points:
        host_path = mount.get('host_path')
        container_path = mount.get('container_path')
        if host_path and container_path:
            print(f"{host_path}:{container_path}")
except Exception as e:
    print(f"Error parsing config: {e}", file=sys.stderr)
    sys.exit(1)
EOF
)

if [ -z "$MOUNTS" ]; then
    echo "No mount points found in configuration"
    VOLUME_ENTRIES=""
else
    # Create volume entries
    VOLUME_ENTRIES=""
    while IFS= read -r MOUNT; do
        VOLUME_ENTRIES="$VOLUME_ENTRIES\n      - $MOUNT:ro"
    done <<< "$MOUNTS"
fi

# Generate docker-compose.yml
cat > docker-compose.yml <<EOF
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: lrmig2
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      dockerfile: docker/Dockerfile
    environment:
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: lrmig2
      DB_USER: postgres
      DB_PASSWORD: postgres
      CONTAINER_CONFIG: /app/$CONFIG_FILE
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app$(echo -e "$VOLUME_ENTRIES")
    command: python -m src.scan_cli --help

volumes:
  postgres_data:
EOF

echo "Generated docker-compose.yml with mounts from $CONFIG_FILE" 