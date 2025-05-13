"""
File: config_loader.py
Purpose: Load configuration from YAML files
Version: 1.1.0
Last Updated: 2024-06-13
"""
import os
import yaml
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Dict with configuration settings
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        yaml.YAMLError: If there's an error parsing the YAML
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        try:
            config = yaml.safe_load(f)
            
            # Translate paths if running in Docker
            if os.environ.get('RUNNING_IN_DOCKER') == 'true':
                translate_paths_for_docker(config)
                
            return config
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML configuration: {e}")

def translate_paths_for_docker(config: Dict[str, Any]) -> None:
    """
    Translate host paths to Docker container paths.
    
    Args:
        config: Configuration dictionary loaded from YAML
    """
    dir_groups = config.get('target_directories', {})
    
    # Map of host paths to container paths
    path_mappings = {}
    
    # Check if we have predefined path mappings in environment
    for env_var in os.environ:
        if env_var.startswith('DOCKER_MOUNT_'):
            parts = os.environ[env_var].split(':')
            if len(parts) == 2:
                host_path, container_path = parts
                path_mappings[host_path] = container_path
    
    # Apply path translations
    for group_name, directories in dir_groups.items():
        for directory in directories:
            host_path = directory.get('path', '')
            if host_path:
                # Check if the path or any parent directory is in the mappings
                best_match = None
                best_match_len = 0
                
                for host_mount, container_mount in path_mappings.items():
                    if host_path.startswith(host_mount) and len(host_mount) > best_match_len:
                        best_match = (host_mount, container_mount)
                        best_match_len = len(host_mount)
                
                if best_match:
                    host_mount, container_mount = best_match
                    rel_path = os.path.relpath(host_path, host_mount)
                    directory['path'] = os.path.join(container_mount, rel_path)

def get_target_directories(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract a flat list of all target directories from the configuration.
    
    Args:
        config: Configuration dictionary loaded from YAML
        
    Returns:
        List of target directory configurations
    """
    targets = []
    
    # Get all directory groups (personal, work, backup, etc.)
    dir_groups = config.get('target_directories', {})
    
    # Flatten the structure into a single list
    for group_name, directories in dir_groups.items():
        for directory in directories:
            # Add group name to each directory config
            directory['group'] = group_name
            targets.append(directory)
    
    return targets

def get_scan_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get scan settings from configuration.
    
    Args:
        config: Configuration dictionary loaded from YAML
        
    Returns:
        Dictionary with scan settings
    """
    return config.get('settings', {}) 