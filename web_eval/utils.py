"""
Utility functions for Web Eval Agent
"""

import logging
import re
import sys
import subprocess
from typing import Optional
from urllib.parse import urlparse


def setup_logging(verbose: bool = False, debug: bool = False) -> None:
    """Setup logging configuration."""
    if debug:
        level = logging.DEBUG
        format_str = "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
    elif verbose:
        level = logging.INFO
        format_str = "%(asctime)s [%(levelname)s] %(message)s"
    else:
        level = logging.WARNING
        format_str = "%(levelname)s: %(message)s"
    
    logging.basicConfig(
        level=level,
        format=format_str,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Suppress noisy loggers
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("browser_use").setLevel(logging.INFO if verbose else logging.WARNING)


def validate_url(url: str) -> bool:
    """Validate URL format."""
    if not url:
        return False
    
    # Add protocol if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    try:
        # Check if playwright browsers are installed
        result = subprocess.run(
            ["python", "-c", "from playwright.sync_api import sync_playwright; sync_playwright().start()"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("❌ Playwright browsers not installed. Run: playwright install")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Dependency check timed out")
        return False
    except FileNotFoundError:
        print("❌ Python not found in PATH")
        return False
    except Exception as e:
        print(f"❌ Dependency check failed: {e}")
        return False


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"


def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to maximum length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem usage."""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        filename = name[:max_name_length] + ('.' + ext if ext else '')
    
    return filename


def get_file_size_mb(filepath: str) -> float:
    """Get file size in megabytes."""
    try:
        import os
        return os.path.getsize(filepath) / (1024 * 1024)
    except (OSError, FileNotFoundError):
        return 0.0


def ensure_directory(filepath: str) -> None:
    """Ensure directory exists for the given filepath."""
    import os
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
