#!/usr/bin/env python3

import os
import dotenv
import pathlib

# Load environment variables from .env file if it exists
env_path = pathlib.Path('.env')
if env_path.exists():
    dotenv.load_dotenv()

def get_backend_url(path: str = "") -> str:
    """
    Get the backend URL based on environment configuration.
    
    Args:
        path: Optional path to append to the base URL
        
    Returns:
        str: The complete backend URL
    """
    # Default to render backend if no .env file or variable is missing
    use_local_env = os.getenv("USE_LOCAL_BACKEND")
    use_local = use_local_env is not None and use_local_env.lower() == "true"
    
    if use_local:
        base_url = "http://0.0.0.0:8000"
    else:
        # Default to render backend
        base_url = "https://operative-backend.onrender.com"
    
    # Remove trailing slash from base_url if present
    if base_url.endswith("/"):
        base_url = base_url[:-1]
    
    # Remove leading slash from path if present
    if path and path.startswith("/"):
        path = path[1:]
    
    # Combine base_url and path
    if path:
        return f"{base_url}/{path}"
    else:
        return base_url
