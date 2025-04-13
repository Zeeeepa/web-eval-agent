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
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If there's an error parsing the YAML
        ValueError: If the YAML content is not a list
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Test file not found: {file_path}")
        
    with open(file_path, 'r') as f:
        tests = yaml.safe_load(f)
        if tests is None:
            raise ValueError(f"YAML file is empty: {file_path}")
        if not isinstance(tests, list):
            raise ValueError(f"YAML content must be a list, got {type(tests)}: {tests}")
        return tests

def save_yaml(file_path: str, data: List[Dict[str, Any]]) -> None:
    """Save test definitions to YAML file.
    
    Args:
        file_path: Path to save the YAML file
        data: List of test definitions to save
        
    Raises:
        IOError: If there's an error writing to the file
        yaml.YAMLError: If there's an error dumping to YAML
    """
    with open(file_path, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False) 