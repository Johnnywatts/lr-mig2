"""
File: config_loader.py
Purpose: Load configuration from YAML files
Version: 1.0.0
Last Updated: 2024-06-13
"""
import os
import yaml
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
            return config
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML configuration: {e}")

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