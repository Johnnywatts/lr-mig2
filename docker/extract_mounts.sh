#!/bin/bash
# Extract mount points from YAML configuration file

set -e

CONFIG_FILE="$1"
if [ -z "$CONFIG_FILE" ]; then
  echo "Usage: $0 <config_file.yaml>"
  exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Config file not found: $CONFIG_FILE"
  exit 1
fi

# Check if python and pyyaml are available
if ! command -v python3 &> /dev/null; then
  echo "Python 3 is required but not found"
  exit 1
fi

# Use Python to extract mount points
python3 - <<EOF
import yaml
import os
import sys

try:
    with open("$CONFIG_FILE", 'r') as f:
        config = yaml.safe_load(f)
    
    mount_points = set()
    
    # Get all directory paths
    dir_groups = config.get('target_directories', {})
    for group_name, directories in dir_groups.items():
        for directory in directories:
            path = directory.get('path', '')
            if path and os.path.isdir(path):
                # Get the top-level directory
                top_dir = os.path.abspath(path)
                while os.path.dirname(top_dir) != '/' and os.path.basename(os.path.dirname(top_dir)) != '':
                    parent = os.path.dirname(top_dir)
                    if os.access(parent, os.R_OK):
                        top_dir = parent
                    else:
                        break
                
                mount_points.add(top_dir)
    
    # Print mount points in docker-compose format
    for i, mount in enumerate(mount_points):
        container_path = f"/data/mount{i}"
        print(f"{mount}:{container_path}")
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
EOF 