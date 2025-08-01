"""
Logging configuration for browser operations

This module provides logging configuration and utilities for browser management.
"""

import logging
import sys
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def setup_browser_logging(level: str = "INFO") -> logging.Logger:
    """Setup logging for browser operations"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    browser_logger = logging.getLogger("web_eval_agent.browser")
    browser_logger.setLevel(log_level)
    
    return browser_logger


def get_browser_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a browser logger instance"""
    if name:
        return logging.getLogger(f"web_eval_agent.browser.{name}")
    return logging.getLogger("web_eval_agent.browser")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance (alias for get_browser_logger)"""
    return get_browser_logger(name)


class StructuredLogger:
    """Structured logger for consistent logging format"""
    
    def __init__(self, name: Optional[str] = None):
        self.logger = get_logger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        if kwargs:
            self.logger.info(f"{message} - {kwargs}")
        else:
            self.logger.info(message)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data"""
        if kwargs:
            self.logger.error(f"{message} - {kwargs}")
        else:
            self.logger.error(message)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data"""
        if kwargs:
            self.logger.warning(f"{message} - {kwargs}")
        else:
            self.logger.warning(message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data"""
        if kwargs:
            self.logger.debug(f"{message} - {kwargs}")
        else:
            self.logger.debug(message)


# Default browser logger
browser_logger = get_browser_logger()
