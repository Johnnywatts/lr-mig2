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

# Function to parse YAML in the bootstrapper
parse_yaml() {
    local yaml_file=$1
    local prefix=$2
    local s
    local w
    local fs

    s='[[:space:]]*'
    w='[a-zA-Z0-9_.-]*'
    fs="$(echo @|tr @ '\034')"

    (
        sed -e '/- [^\"]'"[^\']"'.*: /s|\([ ]*\)- \([^ ]*\): \(.*\)|\1-\n\1  \2: \3|g' |

        sed -ne '/^--/s|--||g; s|\"|\\\"|g; s/[[:space:]]*$//g;' \
            -e "/#.*[\"\']/!s| #.*||g; /^#/s|#.*||g;" \
            -e "s|^\($s\)\($w\)$s:$s\"\(.*\)\"$s\$|\1$fs\2$fs\3|p" \
            -e "s|^\($s\)\($w\)${s}[:-]$s\(.*\)$s\$|\1$fs\2$fs\3|p" |

        awk -F"$fs" '{
            indent = length($1)/2;
            if (indent == 0) {
                printf("\n%s:\n", $2);
            } else {
                vname[indent] = $2;
                for (i in vname) {if (i > indent) {delete vname[i]}}
                if (length($3) > 0) {
                    vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i+1])("_")}
                    printf("%s%s=\"%s\"\n", "'$prefix'",vn$2,$3);
                }
            }
        }'
    ) < "$yaml_file"
}

# Run bootstrapper container to generate docker-compose.yml and start application
echo "Starting Lightroom File Management Utility..."
echo "Using container config: config/container_config.yaml"
echo "Using scan config: config/scan_targets.yaml"

# Extract mount points from config directly in this script
MOUNT_POINTS=""
eval $(parse_yaml config/container_config.yaml "config_")

# Process mount points from parsed YAML
echo "Extracting mount points from configuration..."
if [[ $(grep -c "config_container_mount_points_.*host_path" <<< "$(set)") -gt 0 ]]; then
    # This is a simplified approach - in a real implementation you might need more robust parsing
    for var in $(set | grep "config_container_mount_points_.*host_path" | cut -d= -f1); do
        # Get index from variable name
        idx=$(echo $var | sed -E 's/config_container_mount_points_([0-9]+)_host_path/\1/')
        host_path_var="config_container_mount_points_${idx}_host_path"
        container_path_var="config_container_mount_points_${idx}_container_path"
        
        # Get values
        host_path="${!host_path_var}"
        container_path="${!container_path_var}"
        
        # Add to mount points if both values exist
        if [[ -n "$host_path" && -n "$container_path" ]]; then
            MOUNT_POINTS="${MOUNT_POINTS} -v $host_path:$container_path:ro"
        fi
    done
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
    $MOUNT_POINTS \
    $(docker build -q -f docker/Dockerfile .) \
    python -m src.scan_cli --config="$SCAN_CONFIG" $GROUP $VERBOSE

echo "✅ Scan complete!" 