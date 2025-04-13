#!/usr/bin/env python3

import os
import yaml
from typing import Dict, List, Any

def load_yaml_or_default(file_path: str) -> List[Dict[str, Any]]:
    """Load tests from YAML file or return empty list if file doesn't exist.
    
    Args:
        file_path: Path to the YAML file
        
    Returns:
        List[Dict[str, Any]]: List of test definitions
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                tests = yaml.safe_load(f)
                if not tests or not isinstance(tests, list):
                    return []
                return tests
        return []
    except Exception as e:
        print(f"Error loading YAML file: {e}")
        return []

def save_yaml(file_path: str, data: List[Dict[str, Any]]) -> None:
    """Save test definitions to YAML file.
    
    Args:
        file_path: Path to save the YAML file
        data: List of test definitions to save
    """
    try:
        with open(file_path, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        print(f"Error saving YAML file: {e}") 